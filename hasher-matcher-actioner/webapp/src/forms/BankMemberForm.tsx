/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, SyntheticEvent, useEffect} from 'react';
import {Form, Button, ProgressBar} from 'react-bootstrap';
import {useFormik} from 'formik';
import PreviewableDropzone from './PreviewableDropzone';
import {ContentType} from '../utils/constants';

type BankMemberFormProps = {
  type: ContentType;
  handleSubmit: (file: File, notes: string) => void;
  uploadProgress: number; // Between 0 and 100 implies upload not started, 100 implies uploaded and anything in between is shown in progress bar
};

function renderProgressBar(uploadProgress: number): JSX.Element | null {
  if (uploadProgress === 0) {
    return null;
  }

  return <ProgressBar now={uploadProgress} />;
}

export default function BankMemberForm({
  type,
  handleSubmit,
  uploadProgress,
}: BankMemberFormProps) {
  const [saving, setSaving] = useState(false);

  const formik = useFormik({
    initialValues: {
      file: undefined,
      notes: '',
    },
    onSubmit: values => {
      if (!values.file) {
        return;
      }

      setSaving(true);
      handleSubmit(values.file!, values.notes);
    },
  });

  const innerHandleSubmit = (event: SyntheticEvent) => {
    event.preventDefault();
    formik.submitForm();
  };

  const ctaLabel = type === ContentType.Video ? 'Add Video' : 'Add Photo';

  return (
    <Form onSubmit={innerHandleSubmit}>
      <Form.Group className="mt-4">
        <PreviewableDropzone
          contentType={type}
          file={formik.values.file}
          handleFileChange={(file: File) => formik.setFieldValue('file', file)}
        />
        {renderProgressBar(uploadProgress)}
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label htmlFor="notes">Notes</Form.Label>
        <Form.Control
          id="notes"
          as="textarea"
          rows={3}
          placeholder="Optional description or instructions for other admins. Can be added later."
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          isValid={formik.touched.notes && !formik.errors.notes}
          isInvalid={formik.touched.notes && !!formik.errors.notes}
          value={formik.values.notes}
        />
        {formik.touched.notes && formik.errors.notes ? (
          <Form.Control.Feedback type="invalid">
            {formik.errors.notes}
          </Form.Control.Feedback>
        ) : null}
      </Form.Group>
      <Button type="submit" variant="primary" disabled={saving}>
        {ctaLabel}
      </Button>
    </Form>
  );
}
