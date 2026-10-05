import { useState } from "react"
import AuthProvider from "./context/AuthProvider"
import { useAuth } from "./context/authContext"
import AuthPage from "./pages/AuthPage"

import {
  exportDataset,
  generateDataset,
  inferSchemaFromCsv
} from "./api/datasetApi"

import {
  DEFAULT_CASE_DISTRIBUTION
} from "./constants/caseTypes"

import AppShell from "./components/layout/AppShell"
import CaseConfiguration from "./components/generation/CaseConfiguration"
import DatasetPreview from "./components/generation/DatasetPreview"
import QualityReport from "./components/quality/QualityReport"
import SchemaSourceSelection from "./components/schema/SchemaSourceSelection"
import SchemaSummary from "./components/schema/SchemaSummary"
import UploadSchemaModal from "./components/schema/UploadSchemaModal"

import { useTheme } from "./hooks/useTheme"
import SchemaBuilderPage from "./pages/SchemaBuilderPage"

import {
  buildSchemaPreview,
  convertInferredColumnsToFrontendColumns,
  createEmptyColumn
} from "./utils/schemaUtils"

import {
  getCaseDistributionTotal,
  isCaseDistributionValid,
  validateDatasetRequest,
  validateSchema
} from "./utils/schemaValidation"


const MAXIMUM_ROW_COUNT = 10000

const VIEW_SOURCE = "source"
const VIEW_BUILDER = "builder"
const VIEW_GENERATOR = "generator"


function AuthenticatedApp() {
  const { isDarkMode, toggleTheme } = useTheme()

  const [currentView, setCurrentView] = useState(VIEW_SOURCE)
  const [builderSource, setBuilderSource] = useState("manual")
  const [datasetName, setDatasetName] = useState("")
  const [rowCount, setRowCount] = useState("")
  const [columns, setColumns] = useState([])

  const [caseDistribution, setCaseDistribution] = useState(() => ({
    ...DEFAULT_CASE_DISTRIBUTION
  }))

  const [generatedData, setGeneratedData] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isInferringSchema, setIsInferringSchema] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [activeModal, setActiveModal] = useState(null)

  const caseDistributionTotal = getCaseDistributionTotal(caseDistribution)
  const distributionIsValid = isCaseDistributionValid(caseDistribution)

  const schemaPreview = buildSchemaPreview({
    datasetName,
    rowCount,
    columns,
    caseDistribution
  })

  function clearMessages() {
    setErrorMessage("")
    setSuccessMessage("")
  }

  function openUploadModal() {
    clearMessages()
    setActiveModal("upload")
  }

  function openManualBuilder() {
    clearMessages()
    setBuilderSource("manual")

    if (columns.length === 0) {
      setColumns([createEmptyColumn()])
    }

    setCurrentView(VIEW_BUILDER)
  }

  function closeModal() {
    if (isInferringSchema) {
      return
    }

    setActiveModal(null)
  }

  function returnToSourceSelection() {
    if (isInferringSchema) {
      return
    }

    clearMessages()
    setGeneratedData(null)
    setActiveModal(null)
    setCurrentView(VIEW_SOURCE)
  }

  function openSchemaBuilder() {
    clearMessages()
    setCurrentView(VIEW_BUILDER)
  }

  function addColumn() {
    setColumns((previousColumns) => [
      ...previousColumns,
      createEmptyColumn()
    ])
  }

  function updateColumn(columnId, field, value) {
    setColumns((previousColumns) =>
      previousColumns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              [field]: value
            }
          : column
      )
    )
  }

  function toggleColumnBoolean(columnId, field) {
    setColumns((previousColumns) =>
      previousColumns.map((column) => {
        if (column.id !== columnId) {
          return column
        }

        const nextValue = !column[field]

        if (field === "required") {
          return {
            ...column,
            required: nextValue,
            nullable: nextValue ? false : column.nullable
          }
        }

        if (field === "nullable") {
          return {
            ...column,
            nullable: nextValue,
            required: nextValue ? false : column.required
          }
        }

        return {
          ...column,
          [field]: nextValue
        }
      })
    )
  }

  function deleteColumn(columnId) {
    setColumns((previousColumns) =>
      previousColumns.filter((column) => column.id !== columnId)
    )
  }

  function updateCaseDistribution(field, value) {
    const numericValue = Number(value)

    setCaseDistribution((previousDistribution) => ({
      ...previousDistribution,
      [field]: Number.isNaN(numericValue) ? 0 : numericValue
    }))
  }

  async function handleSchemaInference(event) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setIsInferringSchema(true)
    clearMessages()
    setGeneratedData(null)

    try {
      const result = await inferSchemaFromCsv(file)

      const inferredColumns = convertInferredColumnsToFrontendColumns(
        result.columns || []
      )

      setColumns(inferredColumns)
      setBuilderSource("csv")
      setActiveModal(null)
      setCurrentView(VIEW_BUILDER)

      setSuccessMessage(
        result.message ||
          "Schema inferred successfully. Review the inferred columns before continuing."
      )
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to infer schema from CSV."
      )
    } finally {
      setIsInferringSchema(false)
      event.target.value = ""
    }
  }

  function handleBuilderContinue() {
    if (!datasetName.trim()) {
      setErrorMessage("Dataset name is required.")
      return
    }

    const numericRowCount = Number(rowCount)

    if (
      !numericRowCount ||
      numericRowCount < 1 ||
      numericRowCount > MAXIMUM_ROW_COUNT
    ) {
      setErrorMessage(
        `Row count must be between 1 and ${MAXIMUM_ROW_COUNT.toLocaleString()}.`
      )
      return
    }

    const schemaError = validateSchema(columns)

    if (schemaError) {
      setErrorMessage(schemaError)
      return
    }

    setGeneratedData(null)
    setErrorMessage("")
    setSuccessMessage(
      "Schema validated successfully. Configure test-case percentages and generate the dataset."
    )
    setCurrentView(VIEW_GENERATOR)
  }

  function getRequestValidationError() {
    return validateDatasetRequest({
      datasetName,
      rowCount,
      columns,
      caseDistribution,
      maximumRowCount: MAXIMUM_ROW_COUNT
    })
  }

  async function handleGenerateDataset() {
    const validationError = getRequestValidationError()

    if (validationError) {
      setErrorMessage(validationError)
      setSuccessMessage("")
      return
    }

    setIsGenerating(true)
    clearMessages()
    setGeneratedData(null)

    try {
      const result = await generateDataset(schemaPreview)

      setGeneratedData(result)
      setSuccessMessage("Dataset generated successfully.")
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to generate dataset."
      )
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleExport(format) {
    const validationError = getRequestValidationError()

    if (validationError) {
      setErrorMessage(validationError)
      setSuccessMessage("")
      return
    }

    setIsExporting(true)
    setErrorMessage("")

    try {
      await exportDataset({
        format,
        schemaRequest: schemaPreview,
        datasetName
      })

      setSuccessMessage(
        `${format.toUpperCase()} export downloaded successfully.`
      )
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to export dataset."
      )
    } finally {
      setIsExporting(false)
    }
  }

  function handleNavigationSelect(navigationItem) {
    if (navigationItem === "generator") {
      returnToSourceSelection()
    }
  }

  function getPageDetails() {
    if (currentView === VIEW_BUILDER) {
      return {
        title: "Schema builder",
        description: "Define dataset details, columns, constraints, and generation rules."
      }
    }

    if (currentView === VIEW_GENERATOR) {
      return {
        title: "Generate dataset",
        description: "Configure test coverage, generate rows, inspect quality, and export results."
      }
    }

    return {
      title: "Data generator",
      description: "Create realistic synthetic datasets without using production records."
    }
  }

  function renderHeaderActions() {
    if (currentView === VIEW_SOURCE) {
      return null
    }

    if (currentView === VIEW_BUILDER) {
      return (
        <button
          type="button"
          onClick={returnToSourceSelection}
          className="hidden rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-blue-950 sm:inline-flex"
        >
          Change source
        </button>
      )
    }

    return (
      <div className="hidden flex-wrap gap-2 sm:flex">
        <button
          type="button"
          onClick={openSchemaBuilder}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-blue-950"
        >
          Edit schema
        </button>

        <button
          type="button"
          onClick={returnToSourceSelection}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus:ring-blue-950"
        >
          Change source
        </button>
      </div>
    )
  }

  const pageDetails = getPageDetails()

  return (
    <AppShell
      title={pageDetails.title}
      description={pageDetails.description}
      headerActions={renderHeaderActions()}
      activeNavigationItem="generator"
      isDarkMode={isDarkMode}
      onToggleTheme={toggleTheme}
      onSelectNavigation={handleNavigationSelect}
    >
      <div className="theme-transition min-h-[calc(100vh-73px)]">
        {currentView === VIEW_SOURCE && (
          <SchemaSourceSelection
            onUploadCsv={openUploadModal}
            onCreateManual={openManualBuilder}
          />
        )}

        {currentView === VIEW_BUILDER && (
          <SchemaBuilderPage
            sourceType={builderSource}
            datasetName={datasetName}
            rowCount={rowCount}
            columns={columns}
            errorMessage={errorMessage}
            maximumRowCount={MAXIMUM_ROW_COUNT}
            onDatasetNameChange={setDatasetName}
            onRowCountChange={setRowCount}
            onAddColumn={addColumn}
            onUpdateColumn={updateColumn}
            onToggleColumnBoolean={toggleColumnBoolean}
            onDeleteColumn={deleteColumn}
            onBack={returnToSourceSelection}
            onContinue={handleBuilderContinue}
          />
        )}

        {currentView === VIEW_GENERATOR && (
          <section className="mx-auto max-w-7xl px-6 py-8">
            <div className="mb-6 rounded-3xl border border-blue-200 bg-blue-50 px-6 py-5 dark:border-blue-900 dark:bg-blue-950/40">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                    Schema complete
                  </p>

                  <h2 className="mt-1 text-2xl font-bold text-slate-950 dark:text-white">
                    Configure and generate the dataset
                  </h2>

                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                    Review the schema, configure test-case percentages,
                    and generate the synthetic output.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={openSchemaBuilder}
                  className="rounded-2xl border border-blue-300 bg-white px-5 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-blue-800 dark:bg-slate-900 dark:text-blue-300 dark:hover:bg-slate-800 dark:focus:ring-blue-950"
                >
                  Edit schema
                </button>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <SchemaSummary
                datasetName={datasetName}
                rowCount={rowCount}
                columns={columns}
                schemaPreview={schemaPreview}
                maximumRowCount={MAXIMUM_ROW_COUNT}
                onDatasetNameChange={setDatasetName}
                onRowCountChange={setRowCount}
                onEditSchema={openSchemaBuilder}
              />

              <CaseConfiguration
                caseDistribution={caseDistribution}
                caseDistributionTotal={caseDistributionTotal}
                isDistributionValid={distributionIsValid}
                isGenerating={isGenerating}
                errorMessage={errorMessage}
                successMessage={successMessage}
                onDistributionChange={updateCaseDistribution}
                onGenerate={handleGenerateDataset}
              />
            </div>

            <DatasetPreview
              generatedData={generatedData}
              isExporting={isExporting}
              onExport={handleExport}
            />

            <QualityReport generatedData={generatedData} />
          </section>
        )}

        <UploadSchemaModal
          isOpen={activeModal === "upload"}
          datasetName={datasetName}
          rowCount={rowCount}
          errorMessage={errorMessage}
          isInferringSchema={isInferringSchema}
          maximumRowCount={MAXIMUM_ROW_COUNT}
          onDatasetNameChange={setDatasetName}
          onRowCountChange={setRowCount}
          onFileChange={handleSchemaInference}
          onClose={closeModal}
        />
      </div>
    </AppShell>
  )
}




function AppGate() {
  const { user, loading, logout } = useAuth()
  if (loading) return <div className="grid min-h-screen place-items-center bg-slate-950 text-white">Loading...</div>
  if (!user) return <AuthPage />
  return <>
    <button onClick={logout} className="fixed right-5 top-5 z-50 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-lg dark:bg-white dark:text-slate-900">Sign out</button>
    <AuthenticatedApp />
  </>
}

export default function App() {
  return <AuthProvider><AppGate /></AuthProvider>
}
