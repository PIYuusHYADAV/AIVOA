import { createSlice } from '@reduxjs/toolkit'

const emptyFields = {
  complaint_source: '',
  customer_name: '',
  product_name: '',
  product_strength: '',
  batch_lot_number: '',
  manufacturing_date: '',
  expiry_date: '',
  quantity_affected: '',
  complaint_type: '',
  complaint_date: '',
  description: '',
  severity: '',
  priority: '',
}

const initialState = {
  fields: { ...emptyFields },
  confidence: {},       // field_name -> 0..1, drives the "AI-filled" highlight
  missingFields: [],
  severityReasoning: '',
  rootCauseSuggestion: '',
  capaSuggestion: '',
  summary: '',
  duplicateOf: null,
  duplicateScore: null,
  nextSteps: [],
  precautions: [],
  status: 'Pending Triage',
  savedId: null,
  saving: false,
}

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    fieldChangedManually(state, action) {
      const { field, value } = action.payload
      state.fields[field] = value
      // Manual edits are authoritative -> clear any AI confidence flag on that field
      if (state.confidence[field] !== undefined) {
        state.confidence[field] = 1
      }
    },
    applyAiResult(state, action) {
      const r = action.payload
      state.fields = { ...state.fields, ...r.fields }
      state.confidence = { ...state.confidence, ...r.confidence }
      state.missingFields = r.missing_fields ?? state.missingFields
      state.severityReasoning = r.severity_reasoning ?? state.severityReasoning
      state.rootCauseSuggestion = r.root_cause_suggestion ?? state.rootCauseSuggestion
      state.capaSuggestion = r.capa_suggestion ?? state.capaSuggestion
      state.summary = r.summary ?? state.summary
      state.duplicateOf = r.duplicate_of ?? null
      state.duplicateScore = r.duplicate_score ?? null
      state.nextSteps = r.next_steps ?? state.nextSteps
      state.precautions = r.precautions ?? state.precautions
    },
    applyChatFieldUpdate(state, action) {
      const r = action.payload
      if (r.updated_fields) {
        state.fields = { ...state.fields, ...r.updated_fields }
      }
      if (r.next_steps?.length) state.nextSteps = r.next_steps
      if (r.precautions?.length) state.precautions = r.precautions
    },
    resetForm(state) {
      state.fields = { ...emptyFields }
      state.confidence = {}
      state.missingFields = []
      state.severityReasoning = ''
      state.rootCauseSuggestion = ''
      state.capaSuggestion = ''
      state.summary = ''
      state.duplicateOf = null
      state.duplicateScore = null
      state.nextSteps = []
      state.precautions = []
      state.savedId = null
    },
    savingStarted(state) {
      state.saving = true
    },
    savedSuccessfully(state, action) {
      state.saving = false
      state.savedId = action.payload.id
      state.status = action.payload.status
    },
    saveFailed(state) {
      state.saving = false
    },
  },
})

export const {
  fieldChangedManually,
  applyAiResult,
  applyChatFieldUpdate,
  resetForm,
  savingStarted,
  savedSuccessfully,
  saveFailed,
} = complaintSlice.actions

export default complaintSlice.reducer
