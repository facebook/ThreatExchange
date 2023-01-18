// Copyright (c) Meta Platforms, Inc. and affiliates.

export type Collab = {
  name: string;
  import_as_bank_id: string;
  collab_config_class: string;
  attributes: {[key: string]: string};
};

export type CollabSchemaComplexType = {
  type: 'enum' | 'set';
  possible_values?: Array<string>;
  args?: string;
};

export type CollabSchemaFieldType =
  | 'int'
  | 'str'
  | 'bool'
  | CollabSchemaComplexType;
export type CollabSchema = Record<string, CollabSchemaFieldType>;
