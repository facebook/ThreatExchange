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

    // Setup modal event listeners
    this.setupModalEventListeners(bankTitle, addResultDiv, removeResultDiv);
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

      // Get the content type and file from the form
      const contentType = formData.get('content_type');
      const file = formData.get('file');

      // Create new FormData with the correct structure
      const correctedFormData = new FormData();
      correctedFormData.append(contentType, file);

      const response = await fetch(`/c/bank/${form.dataset.bankName}/content`, {
        method: 'POST',
        body: correctedFormData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderAddResult(data, resultDiv);
    } catch (error) {
      this.renderError(`Error adding content by file: ${error.message}`, resultDiv);
    }
  }

  async handleAddContentByUrl(form, resultDiv, bankTitle) {
    try {
      const formData = new FormData(form);
      const url = formData.get('url');
      const contentType = formData.get('content_type');

      const response = await fetch(`/c/bank/${bankTitle}/content?url=${encodeURIComponent(url)}&content_type=${contentType}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.renderAddResult(data, resultDiv);
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
