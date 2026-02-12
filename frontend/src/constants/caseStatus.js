/**
 * Case status constants matching backend CaseStatus enum.
 */
export const CASE_STATUS = {
  OPEN: 'OPEN',
  IN_PROGRESS: 'IN_PROGRESS',
  DONE: 'DONE',
  CANCEL: 'CANCEL',
};

export const CASE_STATUS_LIST = [
  CASE_STATUS.OPEN,
  CASE_STATUS.IN_PROGRESS,
  CASE_STATUS.DONE,
  CASE_STATUS.CANCEL,
];

export const CASE_STATUS_LABEL = {
  [CASE_STATUS.OPEN]: 'Open',
  [CASE_STATUS.IN_PROGRESS]: 'In Progress',
  [CASE_STATUS.DONE]: 'Done',
  [CASE_STATUS.CANCEL]: 'Cancel',
};
