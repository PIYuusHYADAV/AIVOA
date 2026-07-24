import React from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fieldChangedManually, resetForm, savingStarted, savedSuccessfully, saveFailed } from '../store/complaintSlice'
import { chatReset } from '../store/chatSlice'
import { SECTIONS, FIELD_META } from './formConfig'
import { api } from '../api/client'
import { RotateCcw, Save, AlertTriangle, Sparkles } from 'lucide-react'

function sectionCompletion(fields, section) {
  const filled = section.fields.filter((f) => fields[f] && String(fields[f]).trim().length > 0)
  return filled.length / section.fields.length
}

function severityTint(value) {
  if (value === 'Critical') return 'critical'
  if (value === 'Major') return 'major'
  if (value === 'Minor') return 'minor'
  return null
}

function FormField({ name, fields, confidence, onChange }) {
  const meta = FIELD_META[name]
  const value = fields[name] || ''
  const aiFilled = (confidence[name] ?? 0) > 0 && (confidence[name] ?? 0) < 1
  const tint = (name === 'severity' || name === 'priority') && value ? severityTint(value) : null

  const commonProps = {
    id: `field-${name}`,
    value,
    onChange: (e) => onChange(name, e.target.value),
    className: `field__control${aiFilled ? ' field__control--ai' : ''}${tint ? ` field__control--${tint}` : ''}`,
  }

  return (
    <div className={`field field--${meta.type === 'textarea' ? 'full' : 'half'}`}>
      <label htmlFor={`field-${name}`} className="field__label">
        {meta.label}
        {aiFilled && (
          <span className="field__ai-badge" title="Filled by AI extraction — review before saving">
            <Sparkles size={11} /> AI
          </span>
        )}
      </label>

      {meta.type === 'select' ? (
        <select {...commonProps}>
          <option value="">{value ? value : 'Select...'}</option>
          {meta.options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      ) : meta.type === 'textarea' ? (
        <textarea {...commonProps} rows={4} placeholder="Awaiting AI extraction..." />
      ) : (
        <input
          {...commonProps}
          type={meta.type === 'date' ? 'text' : 'text'}
          placeholder={meta.placeholder || (meta.type === 'date' ? 'DD-MMM-YYYY' : 'Awaiting AI extraction...')}
        />
      )}
    </div>
  )
}

export default function ComplaintForm() {
  const dispatch = useDispatch()
  const complaint = useSelector((s) => s.complaint)
  const { fields, confidence, missingFields, duplicateOf, duplicateScore, saving, savedId, status } = complaint

  const onChange = (name, value) => dispatch(fieldChangedManually({ field: name, value }))

  const onReset = () => {
    dispatch(resetForm())
    dispatch(chatReset())
  }

  const onSave = async () => {
    dispatch(savingStarted())
    try {
      const payload = {
        ...fields,
        ai_missing_fields: missingFields,
        ai_duplicate_of: duplicateOf,
        ai_duplicate_score: duplicateScore,
        ai_root_cause: complaint.rootCauseSuggestion,
        ai_capa: complaint.capaSuggestion,
        ai_summary: complaint.summary,
      }
      const saved = await api.saveComplaint(payload)
      dispatch(savedSuccessfully({ id: saved.id, status: saved.status }))
    } catch (e) {
      dispatch(saveFailed())
      alert(`Could not save complaint: ${e.message}`)
    }
  }

  const severityTintClass = severityTint(fields.severity)

  return (
    <section className="panel form-panel">
      <div className="panel__header">
        <div>
          <h1 className="panel__title">Log Customer Complaint</h1>
          <p className="panel__subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className={`status-pill${severityTintClass ? ` status-pill--${severityTintClass}` : ''}`}>
          {savedId ? status : 'Pending Triage'}
        </span>
      </div>

      {duplicateOf && (
        <div className="banner banner--warning">
          <AlertTriangle size={16} />
          <span>
            This may be a <strong>duplicate</strong> of an existing complaint (similarity {Math.round((duplicateScore || 0) * 100)}%). Review before saving.
          </span>
        </div>
      )}

      <div className="form-body">
        <ol className="workflow-rail" aria-label="Complaint intake progress">
          {SECTIONS.map((section, i) => {
            const pct = sectionCompletion(fields, section)
            const complete = pct === 1
            return (
              <li key={section.id} className="workflow-rail__step">
                <div className={`workflow-rail__dot${complete ? ' workflow-rail__dot--done' : ''}`}>
                  {complete ? '✓' : section.id}
                </div>
                {i < SECTIONS.length - 1 && (
                  <div
                    className="workflow-rail__line"
                    style={{ '--fill': `${Math.round(pct * 100)}%` }}
                  />
                )}
              </li>
            )
          })}
        </ol>

        <div className="form-sections">
          {SECTIONS.map((section) => (
            <div className="form-section" key={section.id}>
              <h2 className="form-section__title">
                <span className="form-section__index">{section.id}</span>
                {section.title.toUpperCase()}
              </h2>
              <div className="form-section__grid">
                {section.fields.map((f) => (
                  <FormField key={f} name={f} fields={fields} confidence={confidence} onChange={onChange} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-footer">
        <button className="btn btn--ghost" onClick={onReset}>
          <RotateCcw size={15} /> Reset Form
        </button>
        <button className="btn btn--primary" onClick={onSave} disabled={saving}>
          <Save size={15} /> {saving ? 'Saving...' : savedId ? 'Update Complaint' : 'Save Complaint'}
        </button>
      </div>
    </section>
  )
}
