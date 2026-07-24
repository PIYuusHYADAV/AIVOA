export const SECTIONS = [
  {
    id: 1,
    title: 'Origin & Customer Details',
    fields: ['complaint_source', 'customer_name'],
  },
  {
    id: 2,
    title: 'Product & Batch Identification',
    fields: ['product_name', 'product_strength', 'batch_lot_number', 'manufacturing_date', 'expiry_date', 'quantity_affected'],
  },
  {
    id: 3,
    title: 'Complaint Details',
    fields: ['complaint_type', 'complaint_date', 'description'],
  },
  {
    id: 4,
    title: 'Initial Assessment & Priority',
    fields: ['severity', 'priority'],
  },
]

export const FIELD_META = {
  complaint_source: {
    label: 'Complaint Source',
    type: 'select',
    options: ['Email', 'Phone Call', 'Customer Portal', 'Field Representative', 'Distributor'],
  },
  customer_name: { label: 'Customer Name', type: 'text' },
  product_name: { label: 'Product Name', type: 'text' },
  product_strength: { label: 'Product Strength / Grade', type: 'text' },
  batch_lot_number: { label: 'Batch / Lot Number', type: 'text' },
  manufacturing_date: { label: 'Manufacturing Date', type: 'date' },
  expiry_date: { label: 'Expiry Date', type: 'date' },
  quantity_affected: { label: 'Quantity Affected', type: 'text', placeholder: 'e.g. 12 kg / 3 boxes' },
  complaint_type: {
    label: 'Complaint Type',
    type: 'select',
    options: [
      'Discoloration', 'Broken Seal / Tamper Evidence', 'Foreign Particle', 'Physical Damage',
      'Missing Label', 'Adverse Event / Reaction', 'Short Fill', 'Odor / Smell Issue',
      'Packaging Defect', 'Efficacy Concern', 'Other',
    ],
  },
  complaint_date: { label: 'Complaint Date', type: 'date' },
  description: { label: 'Detailed Complaint Description', type: 'textarea' },
  severity: { label: 'Initial Severity', type: 'select', options: ['Critical', 'Major', 'Minor'] },
  priority: { label: 'Priority', type: 'select', options: ['High', 'Medium', 'Low'] },
}
