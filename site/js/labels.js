/* labels.js: display names for the condition labels stored in the data. The stored value is unchanged
   (filters, URLs and downloads keep it); only what a reader sees is the display name. */
export const CONDITION_LABELS = {
  long_COVID: 'Long COVID', general: 'Not condition-specific', dysautonomia: 'Dysautonomia', ME_CFS: 'ME/CFS',
  EDS_hypermobility: 'EDS and hypermobility', MCAS: 'MCAS', fibromyalgia: 'Fibromyalgia', migraine: 'Migraine',
  multiple: 'Several conditions', POTS: 'POTS', IBS_gut: 'IBS and gut', small_fiber_neuropathy: 'Small fiber neuropathy',
  autism: 'Autism', 'other patient group': 'Other patient group', orthostatic_hypotension: 'Orthostatic hypotension',
  IBD_gut: 'IBD'
};
export const condLabel = c => (c == null ? '' : (CONDITION_LABELS[c] || String(c).replace(/_/g, ' ')));

// condition labels with fewer findings than this are listed separately and kept off cards, charts and the home map
export const MINOR_LABEL_MAX = 10;
