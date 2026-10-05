from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.db.health import (
    DatabaseHealthResult,
    check_database_health,
)


def create_mock_engine(
    scalar_value=1,
    connection_error=None,
):
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = scalar_value

    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result

    connection_context = AsyncMock()

    if connection_error is None:
        connection_context.__aenter__.return_value = (
            mock_connection
        )
    else:
        connection_context.__aenter__.side_effect = (
            connection_error
        )

    mock_engine = MagicMock()
    mock_engine.connect.return_value = connection_context

    return mock_engine, mock_connection


def test_database_health_result_to_dict():
    result = DatabaseHealthResult(
        status="healthy",
        connected=True,
        message="Database connection is available.",
    )

    assert result.to_dict() == {
        "status": "healthy",
        "connected": True,
        "message": "Database connection is available.",
    }


@pytest.mark.asyncio
async def test_database_health_returns_healthy():
    mock_engine, mock_connection = create_mock_engine(
        scalar_value=1
    )

    result = await check_database_health(mock_engine)

    assert result.status == "healthy"
    assert result.connected is True
    assert result.message == (
        "Database connection is available."
    )

    mock_connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_health_handles_unexpected_result():
    mock_engine, mock_connection = create_mock_engine(
        scalar_value=2
    )

    result = await check_database_health(mock_engine)

    assert result.status == "unhealthy"
    assert result.connected is False
    assert result.message == (
        "Database health query returned "
        "an unexpected result."
    )

    mock_connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_database_health_handles_sqlalchemy_error():
    database_error = OperationalError(
        statement="SELECT 1",
        params=None,
        orig=Exception("Connection failed"),
    )

    mock_engine, _ = create_mock_engine(
        connection_error=database_error
    )

    result = await check_database_health(mock_engine)

    assert result.status == "unhealthy"
    assert result.connected is False
    assert result.message == (
        "Database connection is unavailable."
    )


@pytest.mark.asyncio
async def test_database_health_handles_operating_system_error():
    mock_engine, _ = create_mock_engine(
        connection_error=OSError(
            "Connection refused"
        )
    )

    result = await check_database_health(mock_engine)

    assert result.status == "unhealthy"
    assert result.connected is False
    assert result.message == (
        "Database connection is unavailable."
    )