// Copyright (c) Meta Platforms, Inc. and affiliates.

// Bank Management JavaScript
// Handles all bank-related operations including adding/removing content

class BankManager {
  constructor() {
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // Initialize for each bank
    const banksData = window.banksData || [];
    banksData.forEach(bank => this.setupBankEventListeners(bank.name));
  }

  setupBankEventListeners(bankTitle) {
    // Get form elements
    const addContentFileForm = document.getElementById(`add_content_file_${bankTitle}`);
    const addContentUrlForm = document.getElementById(`add_content_url_${bankTitle}`);
    const addContentHashForm = document.getElementById(`add_content_hash_${bankTitle}`);
    const removeContentUrlForm = document.getElementById(`remove_content_url_${bankTitle}`);
    const removeContentHashForm = document.getElementById(`remove_content_hash_${bankTitle}`);
    const removeContentIdForm = document.getElementById(`remove_content_id_${bankTitle}`);

    const addResultDiv = document.getElementById(`add_result_${bankTitle}`);
    const removeResultDiv = document.getElementById(`remove_result_${bankTitle}`);

    // Add content by file upload
    if (addContentFileForm) {
      addContentFileForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleAddContentByFile(event.target, addResultDiv);
      });
    }

    // Add content by URL
    if (addContentUrlForm) {
      addContentUrlForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleAddContentByUrl(event.target, addResultDiv, bankTitle);
      });
    }

    // Add content by hash
    if (addContentHashForm) {
      addContentHashForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleAddContentByHash(event.target, addResultDiv, bankTitle);
      });
    }

    // Remove content by URL
    if (removeContentUrlForm) {
      removeContentUrlForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleRemoveContentByUrl(event.target, removeResultDiv, bankTitle);
      });
    }

    // Remove content by hash
    if (removeContentHashForm) {
      removeContentHashForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleRemoveContentByHash(event.target, removeResultDiv, bankTitle);
      });
    }

    // Remove content by ID
    if (removeContentIdForm) {
      removeContentIdForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await this.handleRemoveContentById(event.target, removeResultDiv, bankTitle);
      });
    }

    // Metadata checkbox toggle and add/remove row
    this.setupMetadataUI(bankTitle);

    // Setup modal event listeners
    this.setupModalEventListeners(bankTitle, addResultDiv, removeResultDiv);
  }

  setupMetadataUI(bankTitle) {
    const fileCheckbox = document.getElementById(`add_metadata_file_${bankTitle}`);
    const urlCheckbox = document.getElementById(`add_metadata_url_${bankTitle}`);
    const fileFields = document.querySelector(`.metadata-fields-file-${bankTitle}`);
    const urlFields = document.querySelector(`.metadata-fields-url-${bankTitle}`);

    if (fileCheckbox && fileFields) {
      fileCheckbox.addEventListener("change", () => {
        fileFields.style.display = fileCheckbox.checked ? "block" : "none";
      });
    }
    if (urlCheckbox && urlFields) {
      urlCheckbox.addEventListener("change", () => {
        urlFields.style.display = urlCheckbox.checked ? "block" : "none";
      });
    }

    // Add row buttons (delegate from document so dynamically added rows work)
    document.querySelectorAll(`.metadata-kv-add[data-bank-title="${bankTitle}"]`).forEach(btn => {
      btn.addEventListener("click", () => {
        const container = btn.previousElementSibling;
        if (!container || !container.classList.contains("metadata-kv-container")) return;
        const firstRow = container.querySelector(".metadata-kv-row");
        if (!firstRow) return;
        const newRow = firstRow.cloneNode(true);
        newRow.querySelectorAll("input").forEach(i => i.value = "");
        container.appendChild(newRow);
      });
    });

    document.querySelectorAll(`#metadata-section-file-${bankTitle}, #metadata-section-url-${bankTitle}`).forEach(section => {
      section.addEventListener("click", (e) => {
        if (e.target.closest(".metadata-kv-remove")) {
          const row = e.target.closest(".metadata-kv-row");
          const container = row?.parentElement;
          if (container && container.querySelectorAll(".metadata-kv-row").length > 1) {
            row.remove();
          }
        }
      });
    });
  }

  resetMetadata(bankTitle, tab) {
    const checkbox = document.getElementById(`add_metadata_${tab}_${bankTitle}`);
    if (checkbox) checkbox.checked = false;

    const fields = document.querySelector(`.metadata-fields-${tab}-${bankTitle}`);
    if (fields) {
      fields.style.display = "none";
      fields.querySelectorAll(".metadata-content-id, .metadata-content-uri").forEach(
        input => input.value = ""
      );
      const container = fields.querySelector(".metadata-kv-container");
      if (container) {
        const rows = container.querySelectorAll(".metadata-kv-row");
        rows.forEach((row, i) => {
          if (i === 0) {
            row.querySelectorAll("input").forEach(input => input.value = "");
          } else {
            row.remove();
          }
        });
      }
    }
  }

  getNoteFromForm(bankTitle, tab) {
    const form = document.getElementById(`add_content_${tab}_${bankTitle}`);
    if (!form) return null;
    const input = form.querySelector(`.note-input[data-tab="${tab}"]`);
    const val = input?.value?.trim();
    return val || null;
  }

  resetNote(bankTitle, tab) {
    const form = document.getElementById(`add_content_${tab}_${bankTitle}`);
    if (!form) return;
    const input = form.querySelector(`.note-input[data-tab="${tab}"]`);
    if (input) input.value = "";
  }

  getMetadataFromForm(bankTitle, tab) {
    const checkbox = document.getElementById(`add_metadata_${tab}_${bankTitle}`);
    if (!checkbox || !checkbox.checked) return null;

    const section = document.getElementById(`metadata-section-${tab}-${bankTitle}`);
    if (!section) return null;

    const contentId = section.querySelector(".metadata-content-id")?.value?.trim();
    const contentUri = section.querySelector(".metadata-content-uri")?.value?.trim();
    const json = {};
    section.querySelectorAll(".metadata-kv-row").forEach(row => {
      const key = row.querySelector(".metadata-key")?.value?.trim();
      if (key) json[key] = row.querySelector(".metadata-value")?.value?.trim() ?? "";
    });

    const metadata = {};
    if (contentId) metadata.content_id = contentId;
    if (contentUri) metadata.content_uri = contentUri;
    if (Object.keys(json).length) metadata.json = json;
    if (Object.keys(metadata).length === 0) return null;
    return metadata;
  }

  setupModalEventListeners(bankTitle, addResultDiv, removeResultDiv) {
    // File type listener for file upload
    const addContentModal = document.getElementById(`add-content-modal-${bankTitle}`);
    if (addContentModal) {
      addContentModal.addEventListener('shown.bs.modal', () => {
        const fileInput = document.getElementById(`bank-add-file-input-${bankTitle}`);
        const contentTypeSelect = document.getElementById(`bank-add-content-type-${bankTitle}`);

        if (contentTypeSelect) {
          contentTypeSelect.addEventListener('change', (e) => {
            if (e.target.value === 'photo') {
              fileInput.accept = "image/*";
            } else if (e.target.value === 'video') {
              fileInput.accept = "video/*";
            } else {
              fileInput.accept = "file";
            }
          });
        }
      });

      // Clear results when modal is closed
      addContentModal.addEventListener('hidden.bs.modal', () => {
        if (addResultDiv) addResultDiv.innerHTML = '';
      });
    }

    const removeContentModal = document.getElementById(`remove-content-modal-${bankTitle}`);
    if (removeContentModal) {
      removeContentModal.addEventListener('hidden.bs.modal', () => {
        if (removeResultDiv) removeResultDiv.innerHTML = '';
      });
    }
  }

  async handleAddContentByFile(form, resultDiv) {
    try {
      const formData = new FormData(form);
      const contentType = formData.get('content_type');
      const file = formData.get('file');

      const correctedFormData = new FormData();
      correctedFormData.append(contentType, file);

      const metadata = this.getMetadataFromForm(form.dataset.bankName, "file");
      if (metadata) {
        correctedFormData.append("metadata", JSON.stringify(metadata));
      }

      const note = this.getNoteFromForm(form.dataset.bankName, "file");
      if (note) {
        correctedFormData.append("note", note);
      }

      const response = await fetch(`/c/bank/${form.dataset.bankName}/content`, {
        method: 'POST',
        body: correctedFormData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderAddResult(data, resultDiv);
      form.reset();
      this.resetNote(form.dataset.bankName, "file");
      this.resetMetadata(form.dataset.bankName, "file");
    } catch (error) {
      this.renderError(`Error adding content by file: ${error.message}`, resultDiv);
    }
  }

  async handleAddContentByUrl(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const url = formData.get('url');
      const contentType = formData.get('content_type');

      const metadata = this.getMetadataFromForm(bankTitle, "url");
      const note = this.getNoteFromForm(bankTitle, "url");
      const hasBody = metadata || note;
      const bodyObj = {};
      if (metadata) bodyObj.metadata = metadata;
      if (note) bodyObj.note = note;
      const opts = {
        method: 'POST',
        headers: hasBody ? { 'Content-Type': 'application/json' } : {},
        body: hasBody ? JSON.stringify(bodyObj) : undefined
      };
      const query = `url=${encodeURIComponent(url)}&content_type=${encodeURIComponent(contentType)}`;
      const response = await fetch(`/c/bank/${bankTitle}/content?${query}`, opts);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderAddResult(data, resultDiv);
      form.reset();
      this.resetNote(bankTitle, "url");
      this.resetMetadata(bankTitle, "url");
    } catch (error) {
      this.renderError(`Error adding content by URL: ${error.message}`, resultDiv);
    }
  }

  async handleAddContentByHash(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const signalType = formData.get('signal_type');
      const signalValue = formData.get('signal_value');

      const payload = {};
      payload[signalType] = signalValue;

      const note = this.getNoteFromForm(bankTitle, "hash");
      if (note) payload.note = note;

      const response = await fetch(`/c/bank/${bankTitle}/signal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderAddResult(data, resultDiv);
      form.reset();
      this.resetNote(bankTitle, "hash");
    } catch (error) {
      this.renderError(`Error adding content by hash: ${error.message}`, resultDiv);
    }
  }

  async handleRemoveContentByUrl(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const url = formData.get('url');
      const contentType = formData.get('content_type');

      // First find the content
      const findResponse = await fetch(`/ui/bank/${bankTitle}/content/find`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: url,
          content_type: contentType
        })
      });

      if (!findResponse.ok) {
        throw new Error(`HTTP ${findResponse.status}: ${findResponse.statusText}`);
      }

      const findData = await findResponse.json();
      if (findData.content_ids.length === 0) {
        this.renderError('No matching content found for the provided URL', resultDiv);
        return;
      }

      // Remove all found content
      await this.removeMultipleContent(findData.content_ids, resultDiv, bankTitle);
    } catch (error) {
      this.renderError(`Error finding content by URL: ${error.message}`, resultDiv);
    }
  }

  async handleRemoveContentByHash(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const signalType = formData.get('signal_type');
      const signalValue = formData.get('signal_value');

      // First find the content
      const findResponse = await fetch(`/ui/bank/${bankTitle}/content/find`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          signal_type: signalType,
          signal_value: signalValue
        })
      });

      if (!findResponse.ok) {
        throw new Error(`HTTP ${findResponse.status}: ${findResponse.statusText}`);
      }

      const findData = await findResponse.json();
      if (findData.content_ids.length === 0) {
        this.renderError('No matching content found for the provided hash', resultDiv);
        return;
      }

      // Remove all found content
      await this.removeMultipleContent(findData.content_ids, resultDiv, bankTitle);
    } catch (error) {
      this.renderError(`Error finding content by hash: ${error.message}`, resultDiv);
    }
  }

  async handleRemoveContentById(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const contentId = formData.get('content_id');

      const response = await fetch(`/c/bank/${bankTitle}/content/${contentId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderRemoveResult(data, resultDiv, [contentId]);
    } catch (error) {
      this.renderError(`Error removing content by ID: ${error.message}`, resultDiv);
    }
  }

  async removeMultipleContent(contentIds, resultDiv, bankTitle) {
    const results = [];
    for (const contentId of contentIds) {
      try {
        const response = await fetch(`/c/bank/${bankTitle}/content/${contentId}`, {
          method: 'DELETE'
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        results.push({ contentId, success: true, data });
      } catch (error) {
        results.push({ contentId, success: false, error: error.message });
      }
    }
    this.renderRemoveResult({ results }, resultDiv, contentIds);
  }

  renderAddResult(result, targetDiv) {
    targetDiv.innerHTML = `
            <div class="alert alert-success mt-3" role="alert">
                <h5><i class="bi bi-check-circle me-2"></i>Content Added Successfully!</h5>
                <p><strong>Content ID:</strong> ${result.id}</p>
                <h6>Generated Hashes:</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr><th>Signal Type</th><th>Hash Value</th></tr>
                        </thead>
                        <tbody>
                            ${Object.entries(result.signals).map(([key, value]) => `
                                <tr>
                                    <td class="fw-medium">${key}</td>
                                    <td class="font-monospace text-truncate" style="max-width: 300px;" title="${value}">${value}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
  }

  renderRemoveResult(result, targetDiv, contentIds) {
    const successCount = result.results ? result.results.filter(r => r.success).length : (result.deleted || 0);
    targetDiv.innerHTML = `
            <div class="alert alert-${successCount > 0 ? 'success' : 'warning'} mt-3" role="alert">
                <h5><i class="bi bi-${successCount > 0 ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    ${successCount > 0 ? 'Content Removed' : 'Removal Failed'}
                </h5>
                <p><strong>Removed:</strong> ${successCount} content item(s)</p>
                ${contentIds.length > 1 ? `<p><strong>Content IDs:</strong> ${contentIds.join(', ')}</p>` : ''}
            </div>
        `;
  }

  renderError(message, targetDiv) {
    targetDiv.innerHTML = `
            <div class="alert alert-danger mt-3" role="alert">
                <h5><i class="bi bi-exclamation-triangle me-2"></i>Error</h5>
                <p>${message}</p>
            </div>
        `;
  }
}

// Initialize bank manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new BankManager();
});
