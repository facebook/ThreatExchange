/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/**
 * Messages sent received between HMA's bank APIs and the UI.
 */

export type Bank = {
  // Follows hmalib.common.models.bank.Bank
  bank_id: string;
  bank_name: string;
  bank_description: string;
  created_at: Date;
  updated_at: Date;
};
