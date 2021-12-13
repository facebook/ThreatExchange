/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {ContentType} from '../utils/constants';

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

export type BankMember = {
  // Follows hmalib.common.models.bank.BankMember
  bank_id: string;
  bank_member_id: string;
  content_type: ContentType;
  storage_bucket?: string;
  storage_key?: string;
  raw_content?: string;
  preview_url?: string;
  notes: string;
  created_at: Date;
  updated_at: Date;
};

export type BankMemberSignal = {
  bank_id: string;
  bank_member_id: string;
  signal_id: string;
  signal_type: string; // TODO: Convert to enum.
  signal_value: string;
  updated_at: Date;
};

export type BankMemberWithSignals = BankMember & {
  signals: BankMemberSignal[];
};
