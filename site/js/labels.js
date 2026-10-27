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

// source literature names (the stream that brought a paper into the corpus), shown instead of the stored key
export const SOURCE_LABELS = {
  long_COVID: 'Long COVID', autism: 'Autism', post_viral: 'Post-viral illness', migraine: 'Migraine',
  sjogrens: 'Sjogren\'s', EDS_hypermobility: 'EDS and hypermobility', pans_pandas: 'PANS and PANDAS'
};
export const srcLabel = s => (s == null ? '' : (SOURCE_LABELS[s] || condLabel(s)));
// source coverage text for a list of stored source names
export const sourceList = (list, max = 5) => !list.length ? 'Source literature not recorded'
  : `${list.length} source literature${list.length === 1 ? '' : 's'}: ${list.slice(0, max).map(srcLabel).join(', ')}${list.length > max ? ` +${list.length - max} more` : ''}`;

// research theme names (the search stream a finding came from), shown instead of the stored key
export const THEME_LABELS = {
  dysautonomia: 'Dysautonomia', POTS: 'POTS', hyperadrenergic: 'Hyperadrenergic POTS', dysautonomia_subtype: 'Dysautonomia subtypes',
  patient_evidence: 'Patient-reported evidence', ME_CFS: 'ME/CFS', EDS_hypermobility: 'EDS and hypermobility', fibromyalgia: 'Fibromyalgia',
  MCAS_mast: 'MCAS and mast cells', small_fiber: 'Small fiber neuropathy', ibs_intersection: 'IBS', rccx_gene: 'RCCX genes',
  gastroparesis: 'Gastroparesis', autism_intersection: 'Autism', long_covid_auto: 'Long COVID', post_viral: 'Post-viral illness',
  migraine_intersection: 'Migraine', author_augment: 'Added from key authors', sjogrens: 'Sjogren\'s',
  hypermobility_spectrum: 'Hypermobility spectrum', pans_pandas: 'PANS and PANDAS'
};
export const themeLabel = t => (t == null ? '' : (THEME_LABELS[t] || String(t).replace(/_/g, ' ')));

// condition labels with fewer findings than this are listed separately and kept off cards, charts and the home map
export const MINOR_LABEL_MAX = 10;
