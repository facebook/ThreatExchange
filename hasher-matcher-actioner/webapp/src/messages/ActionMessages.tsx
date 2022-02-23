/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

export type Label = {
  key: string;
  value: string;
};

export type ActionRule = {
  name: string;
  must_have_labels: Label[];
  // Note this is not supported at the moment.
  must_not_have_labels: Label[];
  action_label: Label;
};
