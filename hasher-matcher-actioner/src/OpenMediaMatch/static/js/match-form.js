// Copyright (c) Meta Platforms, Inc. and affiliates.

// Match Form JavaScript
// Handles file upload and URL matching functionality

class MatchForm {
  constructor() {
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    const matchFileForm = document.getElementById("match_file");
    const matchUrlForm = document.getElementById("match_url");
    const matchHashForm = document.getElementById("match_hash");
    const bypassCheckbox = document.getElementById("bypass-enabled-ratio");
    const matches = document.getElementById("matches");

    if (!matchFileForm || !matchUrlForm || !matchHashForm || !bypassCheckbox || !matches) {
      console.warn('Match form elements not found');
      return;
    }

    // Listen for checkbox changes
    bypassCheckbox.addEventListener('change', this.toggleWarning.bind(this));

    // Handle file upload form submission
    matchFileForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await this.handleFileSubmission(event);
    });

    // Handle URL form submission
    matchUrlForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await this.handleUrlSubmission(event);
    });

    // Handle hash form submission
    matchHashForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await this.handleHashSubmission(event);
    });
  }

  toggleWarning() {
    const bypassCheckbox = document.getElementById("bypass-enabled-ratio");
    const warningDiv = document.getElementById("bypass-warning");

    if (bypassCheckbox.checked) {
      warningDiv.style.display = "block";
    } else {
      warningDiv.style.display = "none";
    }
  }

  async handleFileSubmission(event) {
    const formData = new FormData();
    const fileInput = event.target.querySelector('input[name="file"]');
    const contentTypeInput = event.target.querySelector('select[name="media"]');
    const bypassCheckbox = document.getElementById("bypass-enabled-ratio");

    if (!fileInput.files[0]) {
      this.renderError('Please select a file');
      return;
    }

    if (!contentTypeInput.value) {
      this.renderError('Please select a content type');
      return;
    }



    // The content type must be the field name for the file upload
    formData.append(contentTypeInput.value, fileInput.files[0]);
    formData.append('bypass_enabled_ratio', bypassCheckbox.checked);

    await this.submitMatchRequest(formData, false);
  }

  async handleUrlSubmission(event) {
    const formData = new FormData();
    const urlInput = event.target.querySelector('input[name="url"]');
    const contentTypeInput = event.target.querySelector('select[name="media"]');
    const bypassCheckbox = document.getElementById("bypass-enabled-ratio");

    if (!urlInput.value) {
      this.renderError('Please enter a URL');
      return;
    }

    if (!contentTypeInput.value) {
      this.renderError('Please select a content type');
      return;
    }

    // For URL matching, we need to send the URL and content type as parameters
    formData.append('url', urlInput.value);
    formData.append('content_type', contentTypeInput.value);
    formData.append('bypass_enabled_ratio', bypassCheckbox.checked);

    await this.submitMatchRequest(formData, true);
  }

  async handleHashSubmission(event) {
    const formData = new FormData();
    const signalTypeInput = event.target.querySelector('select[name="signal_type"]');
    const signalValueInput = event.target.querySelector('input[name="signal_value"]');
    const bypassCheckbox = document.getElementById("bypass-enabled-ratio");

    if (!signalTypeInput.value) {
      this.renderError('Please select a signal type');
      return;
    }

    if (!signalValueInput.value.trim()) {
      this.renderError('Please enter a hash value');
      return;
    }

    // Validate hash format (hexadecimal)
    const hashValue = signalValueInput.value.trim();
    if (!/^[a-fA-F0-9]+$/.test(hashValue)) {
      this.renderError('Please enter a valid hexadecimal hash value (only letters a-f and numbers 0-9)');
      return;
    }

    // For hash matching, we need to send the signal type and value as parameters
    formData.append('signal_type', signalTypeInput.value);
    formData.append('signal_value', signalValueInput.value.trim());
    formData.append('bypass_enabled_ratio', bypassCheckbox.checked);

    await this.submitMatchRequest(formData, false, true);
  }

  async submitMatchRequest(formData, isUrl = false, isHash = false) {
    const matches = document.getElementById("matches");
    let endpoint;

    if (isUrl) {
      endpoint = '/ui/query_url';
    } else if (isHash) {
      endpoint = '/ui/query_hash';
    } else {
      endpoint = '/ui/query';
    }

    try {
      matches.innerHTML = `
                <div class="alert alert-info mt-3" role="alert">
                    <h5><i class="bi bi-hourglass-split me-2"></i>Searching...</h5>
                    <p>Please wait while we search for matches...</p>
                </div>
            `;

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      await this.renderMatchResult(data);
      this.highlightMatchedResults(data);
    } catch (error) {
      console.error('Error:', error);
      this.renderError(`Failed to find matches: ${error.message}`);
    }
  }

  async renderMatchResult(result) {
    const matches = document.getElementById("matches");

    // Fetch bank data with enabled ratios
    const bankData = await this.fetchBankData(result.banks);

    // Render detailed matches if available, otherwise fall back to simple bank list
    let matchesContent = '';
    // Render detailed matches with content IDs and distances
    const matchesList = result.matches.map(match => {
      const bank = bankData[match.bank_name];
      const enabledRatio = bank ? (bank.matching_enabled_ratio * 100).toFixed(1) : 'Unknown';
      const badgeClass = bank && bank.matching_enabled_ratio < 1.0 ? 'bg-warning' : 'bg-success';
      const showBadge = bank && bank.matching_enabled_ratio < 1.0;

      return `
          <li class="list-group-item d-flex justify-content-between align-items-start">
            <div class="ms-2 me-auto">
              <div class="fw-bold">${match.bank_name}</div>
              <small class="text-muted">
                Content ID: ${match.content_id} | Signal: ${match.signal_type}
              </small>
            </div>
            <div class="d-flex flex-column align-items-end">
              <span class="badge ${badgeClass} rounded-pill mb-1" title="${showBadge ? `This bank is only partially enabled, and may not count as matching in production based on coinflip. Enable the bank at 100% to ensure it matches consistently.` : ''}">
                ${enabledRatio}%
              </span>
              <span class="badge bg-info rounded-pill" title="Match distance (lower is better)">
                Distance: ${match.distance}
              </span>
            </div>
          </li>
        `;
    }).join('');

    matchesContent = `
        <h5 class="card-title">Detailed Matches</h5>
        <ul class="list-group list-group-flush mb-3">${matchesList}</ul>
      `;

    const content = `
      <div class="card-body">
        ${matchesContent}
        <h5 class="card-title">Hash Values:</h5>
        <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
          <table class="table table-hover table-sm">
            <thead class="table-light sticky-top">
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              ${Object.entries(result.hashes).map(([key, value]) => `
                <tr>
                  <td class="fw-medium">${key}</td>
                  <td class="font-monospace text-truncate" style="max-width: 200px;" title="${value}">${value}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <button type="button" class="btn btn-secondary mt-3" onclick="matchForm.clearMatches()">Clear</button>
      </div>
    `;

    matches.innerHTML = content;
  }

  async fetchBankData(bankNames) {
    try {
      const bankPromises = bankNames.map(bankName =>
        fetch(`/c/bank/${bankName}`)
          .then(response => response.json())
          .catch(error => {
            console.error(`Error fetching bank ${bankName}:`, error);
            return { name: bankName, matching_enabled_ratio: 'Unknown' };
          })
      );

      const bankDataArray = await Promise.all(bankPromises);
      return bankDataArray.reduce((acc, bankData) => {
        acc[bankData.name] = bankData;
        return acc;
      }, {});
    } catch (error) {
      console.error('Error fetching bank data:', error);
      return {};
    }
  }

  highlightMatchedResults(result) {
    // Render matched banks
    result.banks.forEach((bankName) => {
      const bankElement = document.getElementById(`bank_item_${bankName}`);
      if (bankElement) {
        bankElement.classList.add("bg-light");
      }
    });
  }

  clearMatches() {
    const matches = document.getElementById("matches");
    const banks = document.querySelectorAll('[id^="bank_item_"]');

    matches.innerHTML = "";
    banks.forEach((bankElement) => {
      bankElement.classList.remove("bg-light");
    });
  }

  renderError(message) {
    const matches = document.getElementById("matches");
    matches.innerHTML = `
            <div class="alert alert-danger mt-3" role="alert">
                <h5><i class="bi bi-exclamation-triangle me-2"></i>Error</h5>
                <p>${message}</p>
            </div>
        `;
  }
}

// Initialize match form when DOM is loaded
let matchForm;
document.addEventListener('DOMContentLoaded', () => {
  matchForm = new MatchForm();
});
