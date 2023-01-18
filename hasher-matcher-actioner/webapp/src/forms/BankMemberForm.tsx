/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, SyntheticEvent} from 'react';
import {Form, Button, ProgressBar} from 'react-bootstrap';
import {useFormik} from 'formik';
import PreviewableDropzone from './PreviewableDropzone';
import {ContentType} from '../utils/constants';
import PillBox from '../components/PillBox';

type BankMemberFormProps = {
  type: ContentType;
  handleSubmit: (file: File, notes: string, tags: string[]) => void;
  uploadProgress: number; // Between 0 and 100 implies upload not started, 100 implies uploaded and anything in between is shown in progress bar
};

const ARE_BANK_MEMBER_TAGS_EDITABLE = false;

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
}: BankMemberFormProps): JSX.Element {
  const [saving, setSaving] = useState(false);

  const formik = useFormik({
    initialValues: {
      file: undefined,
      notes: '',
      tags: [] as string[],
    },
    onSubmit: values => {
      if (!values.file) {
        return;
      }

      setSaving(true);
      handleSubmit(values.file!, values.notes, values.tags);
    },
  });

  const innerHandleSubmit = (event: SyntheticEvent) => {
    event.preventDefault();
    formik.submitForm();
  };

  const ctaLabel = type === ContentType.Video ? 'Add Video' : 'Add Photo';

  return (
    <Form className="hma-themed-form" onSubmit={innerHandleSubmit}>
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

        {ARE_BANK_MEMBER_TAGS_EDITABLE ? (
          <>
            <Form.Label>Tags</Form.Label>
            <PillBox
              handleNewTagAdd={tag => {
                const alreadyExists = formik.values.tags.indexOf(tag) !== -1;
                if (!alreadyExists) {
                  formik.setFieldValue(
                    'tags',
                    formik.values.tags.concat([tag]),
                  );
                }
              }}
              handleTagDelete={tag => {
                const alreadyExists = formik.values.tags.indexOf(tag) !== -1;
                if (alreadyExists) {
                  formik.setFieldValue(
                    'tags',
                    formik.values.tags.filter(x => x !== tag),
                  );
                }
              }}
              pills={formik.values.tags}
            />
          </>
        ) : null}
      </Form.Group>
      <Button type="submit" variant="primary" disabled={saving}>
        {ctaLabel}
      </Button>
    </Form>
  );
}
