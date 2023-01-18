/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
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
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  bank_tags: string[];
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
  is_media_unavailable: boolean;
  is_removed: boolean;
  bank_member_tags: string[];
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
