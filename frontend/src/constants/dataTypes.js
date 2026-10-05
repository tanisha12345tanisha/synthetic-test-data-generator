export const DATA_TYPES = [
  "string",
  "integer",
  "number",
  "decimal",
  "float",
  "boolean",
  "date",
  "datetime",
  "timestamp",
  "category",
  "name",
  "first_name",
  "last_name",
  "email",
  "phone",
  "address",
  "city",
  "state",
  "country",
  "postal_code",
  "zip",
  "company",
  "job_title",
  "uuid",
  "id",
  "url",
  "ip_address",
  "currency_code",
  "currency_amount",
  "long_text",
  "regex"
]


export const DATA_TYPE_GROUPS = [
  {
    key: "common",
    label: "Common",
    description: "Frequently used general-purpose fields",
    types: [
      {
        value: "string",
        label: "Text",
        shortLabel: "Text",
        description: "Short text values",
        icon: "Aa"
      },
      {
        value: "integer",
        label: "Integer",
        shortLabel: "Integer",
        description: "Whole numbers",
        icon: "123"
      },
      {
        value: "decimal",
        label: "Decimal",
        shortLabel: "Decimal",
        description: "Numbers with decimal places",
        icon: "1.2"
      },
      {
        value: "boolean",
        label: "Boolean",
        shortLabel: "Boolean",
        description: "True or false values",
        icon: "T/F"
      },
      {
        value: "date",
        label: "Date",
        shortLabel: "Date",
        description: "Calendar date without time",
        icon: "D"
      },
      {
        value: "datetime",
        label: "Date and time",
        shortLabel: "DateTime",
        description: "Date and time value",
        icon: "DT"
      }
    ]
  },
  {
    key: "identity",
    label: "Identity and keys",
    description: "Identifiers and structured keys",
    types: [
      {
        value: "id",
        label: "Generated ID",
        shortLabel: "ID",
        description: "Sequential identifier with a prefix",
        icon: "ID"
      },
      {
        value: "uuid",
        label: "UUID",
        shortLabel: "UUID",
        description: "Universally unique identifier",
        icon: "U"
      }
    ]
  },
  {
    key: "personal",
    label: "People and contact",
    description: "Personal and communication fields",
    types: [
      {
        value: "name",
        label: "Full name",
        shortLabel: "Name",
        description: "First and last name",
        icon: "N"
      },
      {
        value: "first_name",
        label: "First name",
        shortLabel: "First Name",
        description: "Single-word first name",
        icon: "FN"
      },
      {
        value: "last_name",
        label: "Last name",
        shortLabel: "Last Name",
        description: "Single-word surname",
        icon: "LN"
      },
      {
        value: "email",
        label: "Email address",
        shortLabel: "Email",
        description: "Valid email address",
        icon: "@"
      },
      {
        value: "phone",
        label: "Phone number",
        shortLabel: "Phone",
        description: "Indian mobile number",
        icon: "P"
      },
      {
        value: "address",
        label: "Address",
        shortLabel: "Address",
        description: "Formatted street address",
        icon: "A"
      }
    ]
  },
  {
    key: "location",
    label: "Location",
    description: "Geographic and postal fields",
    types: [
      {
        value: "city",
        label: "City",
        shortLabel: "City",
        description: "City or town",
        icon: "C"
      },
      {
        value: "state",
        label: "State",
        shortLabel: "State",
        description: "State or province",
        icon: "S"
      },
      {
        value: "country",
        label: "Country",
        shortLabel: "Country",
        description: "Country name",
        icon: "CO"
      },
      {
        value: "postal_code",
        label: "Postal code",
        shortLabel: "Postal Code",
        description: "Indian six-digit postal code",
        icon: "PIN"
      },
      {
        value: "zip",
        label: "ZIP code",
        shortLabel: "ZIP",
        description: "Postal or ZIP code",
        icon: "ZIP"
      }
    ]
  },
  {
    key: "business",
    label: "Business and financial",
    description: "Company, employment, and money fields",
    types: [
      {
        value: "company",
        label: "Company",
        shortLabel: "Company",
        description: "Organization or company name",
        icon: "CO"
      },
      {
        value: "job_title",
        label: "Job title",
        shortLabel: "Job Title",
        description: "Professional role or designation",
        icon: "JT"
      },
      {
        value: "currency_code",
        label: "Currency code",
        shortLabel: "Currency",
        description: "Currency code such as INR",
        icon: "INR"
      },
      {
        value: "currency_amount",
        label: "Currency amount",
        shortLabel: "Amount",
        description: "Non-negative monetary amount",
        icon: "₹"
      }
    ]
  },
  {
    key: "advanced",
    label: "Advanced",
    description: "Special formats and generation rules",
    types: [
      {
        value: "number",
        label: "Number",
        shortLabel: "Number",
        description: "General numeric value",
        icon: "#"
      },
      {
        value: "float",
        label: "Floating-point number",
        shortLabel: "Float",
        description: "Floating-point numeric value",
        icon: "F"
      },
      {
        value: "timestamp",
        label: "Timestamp",
        shortLabel: "Timestamp",
        description: "ISO date and time",
        icon: "TS"
      },
      {
        value: "category",
        label: "Category",
        shortLabel: "Category",
        description: "Value selected from an allowed list",
        icon: "CAT"
      },
      {
        value: "long_text",
        label: "Long text",
        shortLabel: "Long Text",
        description: "Paragraph or description text",
        icon: "TXT"
      },
      {
        value: "url",
        label: "URL",
        shortLabel: "URL",
        description: "HTTP or HTTPS web address",
        icon: "URL"
      },
      {
        value: "ip_address",
        label: "IP address",
        shortLabel: "IP",
        description: "Valid IPv4 or IPv6 address",
        icon: "IP"
      },
      {
        value: "regex",
        label: "Regular expression",
        shortLabel: "Regex",
        description: "Value generated from a regex pattern",
        icon: ".*"
      }
    ]
  }
]


export const COMMON_DATA_TYPES = [
  "string",
  "integer",
  "decimal",
  "boolean",
  "date",
  "email",
  "id",
  "category"
]


export const NUMERIC_TYPES = new Set([
  "integer",
  "number",
  "decimal",
  "float",
  "currency_amount"
])


export const LENGTH_TYPES = new Set([
  "string",
  "long_text",
  "name",
  "first_name",
  "last_name",
  "address",
  "company",
  "job_title"
])


export const DATE_TIME_TYPES = new Set([
  "date",
  "datetime",
  "timestamp"
])


export const BOOLEAN_TYPES = new Set([
  "boolean"
])


export const RESERVED_COLUMN_NAMES = new Set([
  "__case_type",
  "__case_labels",
  "__case_reasons"
])


const DATA_TYPE_DETAILS = new Map(
  DATA_TYPE_GROUPS.flatMap((group) =>
    group.types.map((type) => [
      type.value,
      {
        ...type,
        groupKey: group.key,
        groupLabel: group.label
      }
    ])
  )
)


const TYPE_SUGGESTION_RULES = [
  {
    type: "first_name",
    patterns: [
      /^first_?name$/,
      /^firstname$/,
      /^given_?name$/
    ]
  },
  {
    type: "last_name",
    patterns: [
      /^last_?name$/,
      /^lastname$/,
      /^surname$/,
      /^family_?name$/
    ]
  },
  {
    type: "name",
    patterns: [
      /^name$/,
      /^full_?name$/,
      /^customer_?name$/,
      /^employee_?name$/,
      /^person_?name$/
    ]
  },
  {
    type: "email",
    patterns: [
      /email/,
      /e_?mail/
    ]
  },
  {
    type: "phone",
    patterns: [
      /phone/,
      /mobile/,
      /contact_?number/
    ]
  },
  {
    type: "address",
    patterns: [
      /address/,
      /street/
    ]
  },
  {
    type: "city",
    patterns: [
      /^city$/,
      /^town$/
    ]
  },
  {
    type: "state",
    patterns: [
      /^state$/,
      /^province$/
    ]
  },
  {
    type: "country",
    patterns: [
      /^country$/
    ]
  },
  {
    type: "postal_code",
    patterns: [
      /postal_?code/,
      /pin_?code/,
      /^pincode$/,
      /^zip_?code$/,
      /^zipcode$/
    ]
  },
  {
    type: "currency_code",
    patterns: [
      /currency_?code/,
      /^currency$/,
      /^ccy$/
    ]
  },
  {
    type: "currency_amount",
    patterns: [
      /amount/,
      /balance/,
      /price/,
      /cost/,
      /salary/,
      /fee/
    ]
  },
  {
    type: "boolean",
    patterns: [
      /^is_/,
      /^has_/,
      /^can_/,
      /^enabled$/,
      /^active$/,
      /^verified$/
    ]
  },
  {
    type: "timestamp",
    patterns: [
      /timestamp/,
      /created_?at/,
      /updated_?at/,
      /processed_?at/
    ]
  },
  {
    type: "datetime",
    patterns: [
      /date_?time/,
      /datetime/
    ]
  },
  {
    type: "date",
    patterns: [
      /date_of_birth/,
      /^dob$/,
      /birth_?date/,
      /start_?date/,
      /end_?date/,
      /opened_?date/,
      /closed_?date/,
      /_date$/
    ]
  },
  {
    type: "uuid",
    patterns: [
      /uuid/,
      /guid/
    ]
  },
  {
    type: "url",
    patterns: [
      /url/,
      /website/,
      /link/
    ]
  },
  {
    type: "ip_address",
    patterns: [
      /ip_?address/,
      /_ip$/
    ]
  },
  {
    type: "company",
    patterns: [
      /company/,
      /organization/,
      /employer/
    ]
  },
  {
    type: "job_title",
    patterns: [
      /job_?title/,
      /designation/,
      /profession/,
      /^role$/
    ]
  },
  {
    type: "id",
    patterns: [
      /^id$/,
      /_id$/,
      /^id_/
    ]
  },
  {
    type: "category",
    patterns: [
      /status/,
      /type$/,
      /category/,
      /segment/
    ]
  }
]


export function getDataTypeDetails(type) {
  return DATA_TYPE_DETAILS.get(type) || {
    value: type,
    label: type || "Select type",
    shortLabel: type || "Select type",
    description: "",
    icon: "?",
    groupKey: "other",
    groupLabel: "Other"
  }
}


export function suggestDataType(columnName) {
  const normalizedName = String(columnName || "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")

  if (!normalizedName) {
    return ""
  }

  const matchedRule = TYPE_SUGGESTION_RULES.find((rule) =>
    rule.patterns.some((pattern) =>
      pattern.test(normalizedName)
    )
  )

  return matchedRule?.type || "string"
}


export function supportsNumericRange(type) {
  return NUMERIC_TYPES.has(type)
}


export function supportsLengthRange(type) {
  return LENGTH_TYPES.has(type)
}


export function supportsCategoryValues(type) {
  return type === "category"
}


export function supportsPrefix(type) {
  return type === "id"
}


export function supportsPattern(type) {
  return type === "regex"
}


export function supportsDateRange(type) {
  return DATE_TIME_TYPES.has(type)
}


export function supportsBooleanProbability(type) {
  return BOOLEAN_TYPES.has(type)
}


export function hasAdvancedFields(type) {
  return (
    supportsNumericRange(type) ||
    supportsLengthRange(type) ||
    supportsCategoryValues(type) ||
    supportsPrefix(type) ||
    supportsPattern(type) ||
    supportsDateRange(type) ||
    supportsBooleanProbability(type)
  )
}