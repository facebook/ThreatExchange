// Copyright (c) Meta Platforms, Inc. and affiliates.
// Create Exchange modal: schema-driven config and credential fields.

(function () {
    function init() {
        const form = document.getElementById('exchange_create_form');
        const apiSelect = document.getElementById('exchange_create_form_api');
        const bankInput = document.getElementById('exchange_create_form_bank');
        const configSection = document.getElementById('exchange_create_config_section');
        const configFieldsContainer = document.getElementById('exchange_create_config_fields');
        const credentialsSection = document.getElementById('exchange_create_credentials_section');
        const credentialFieldsContainer = document.getElementById('exchange_create_credential_fields');
        const submitBtn = document.getElementById('exchange_create_form_submit');
        const bankNameError = document.getElementById('bank-name-error');

        if (!form || !apiSelect) return;

        let currentSchema = null;

        function setSchemaInputAttrs(el, id, field, prefix) {
            el.id = id;
            el.name = prefix + '.' + field.name;
            el.dataset.schemaType = field.type || 'string';
            el.dataset.schemaName = field.name;
            return el;
        }

        function createInputForField(field, id, prefix) {
            let input;
            if (field.type === 'enum' && Array.isArray(field.choices)) {
                input = document.createElement('select');
                input.className = 'form-select form-select-sm';
                const empty = document.createElement('option');
                empty.value = '';
                empty.textContent = field.required ? '— Select —' : '— Optional —';
                input.appendChild(empty);
                field.choices.forEach(function (v) {
                    const opt = document.createElement('option');
                    opt.value = v;
                    opt.textContent = v;
                    input.appendChild(opt);
                });
            } else if (field.type === 'boolean') {
                input = document.createElement('input');
                input.type = 'checkbox';
                input.className = 'form-check-input';
                if (field.default === true) input.checked = true;
            } else if (field.type === 'number' || field.type === 'set_of_number') {
                input = document.createElement('input');
                input.type = field.type === 'number' ? 'number' : 'text';
                input.className = 'form-control form-control-sm';
                if (field.default != null) {
                    input.value =
                        field.type === 'set_of_number'
                            ? Array.isArray(field.default)
                                ? field.default.join(', ')
                                : ''
                            : String(field.default);
                }
                if (field.type === 'set_of_number') input.placeholder = 'e.g. 1, 2, 3';
            } else {
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control form-control-sm';
                if (field.default != null) input.value = String(field.default);
            }
            return setSchemaInputAttrs(input, id, field, prefix);
        }

        function renderField(container, field, prefix, sectionOptional) {
            sectionOptional = sectionOptional || false;
            const id = prefix + '_' + field.name;
            const wrap = document.createElement('div');
            wrap.className = 'mb-2';
            const label = document.createElement('label');
            label.className = 'form-label small';
            label.htmlFor = id;
            const labelText = field.name.replace(/_/g, ' ');
            label.textContent = labelText.charAt(0).toUpperCase() + labelText.slice(1);
            if (field.required && !sectionOptional)
                label.innerHTML += ' <span class="text-danger">*</span>';
            wrap.appendChild(label);
            if (field.help) {
                const help = document.createElement('div');
                help.className = 'form-text small text-muted';
                help.textContent = field.help;
                wrap.appendChild(help);
            }
            wrap.appendChild(createInputForField(field, id, prefix));
            container.appendChild(wrap);
        }

        function buildObjectFromFields(container, prefix) {
            const obj = {};
            container.querySelectorAll('[data-schema-name]').forEach(function (el) {
                const name = el.dataset.schemaName;
                const type = el.dataset.schemaType || 'string';
                let val;
                if (type === 'boolean') {
                    val = el.checked;
                } else {
                    val = el.value.trim();
                    if (val === '') return;
                    if (type === 'number') val = Number(val);
                    else if (type === 'set_of_number') {
                        val = val
                            .split(',')
                            .map(function (s) {
                                return parseInt(s.trim(), 10);
                            })
                            .filter(function (n) {
                                return !isNaN(n);
                            });
                        val = val.length ? val : undefined;
                    }
                    if (val === undefined) return;
                }
                obj[name] = val;
            });
            return obj;
        }

        function onApiChange() {
            const api = apiSelect.value;
            configFieldsContainer.innerHTML = '';
            credentialFieldsContainer.innerHTML = '';
            configSection.style.display = 'none';
            credentialsSection.style.display = 'none';
            currentSchema = null;
            if (!api) return;

            fetch('/c/exchanges/api/' + encodeURIComponent(api) + '/schema', {
                headers: { Accept: 'application/json' },
            })
                .then(function (r) {
                    return r.ok ? r.json() : null;
                })
                .then(function (schema) {
                    currentSchema = schema;
                    if (!schema) return;

                    const configFields =
                        schema.config_schema && schema.config_schema.fields
                            ? schema.config_schema.fields
                            : [];
                    if (configFields.length > 0) {
                        configFields.forEach(function (f) {
                            renderField(configFieldsContainer, f, 'cfg');
                        });
                        configSection.style.display = 'block';
                    } else {
                        configSection.style.display = 'none';
                    }

                    const credFields =
                        schema.credentials_schema && schema.credentials_schema.fields
                            ? schema.credentials_schema.fields
                            : [];
                    if (credFields.length > 0) {
                        credFields.forEach(function (f) {
                            renderField(credentialFieldsContainer, f, 'cred', true);
                        });
                        credentialsSection.style.display = 'block';
                    }
                });
        }

        apiSelect.addEventListener('change', onApiChange);

        if (bankInput) {
            bankInput.addEventListener('blur', function () {
                bankInput.value = bankInput.value.trim().toUpperCase();
                if (bankNameError) bankNameError.textContent = '';
                const regex = /^[A-Z0-9_]+$/;
                if (bankInput.value.trim() === '') {
                    if (bankNameError)
                        bankNameError.textContent = 'This field is required!';
                    bankInput.classList.add('is-invalid');
                } else if (!regex.test(bankInput.value)) {
                    if (bankNameError)
                        bankNameError.textContent =
                            'Bank name must be all uppercase and snake case (e.g. MY_BANK)';
                    bankInput.classList.add('is-invalid');
                } else {
                    bankInput.classList.remove('is-invalid');
                }
            });
        }

        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            const api = apiSelect.value;
            const bank = bankInput ? bankInput.value.trim().toUpperCase() : '';
            if (!api || !bank) return;

            const hasConfigFields =
                currentSchema &&
                currentSchema.config_schema &&
                currentSchema.config_schema.fields &&
                currentSchema.config_schema.fields.length > 0;
            const api_json = hasConfigFields
                ? buildObjectFromFields(configFieldsContainer, 'cfg')
                : {};

            const credential_json =
                currentSchema &&
                currentSchema.credentials_schema &&
                credentialFieldsContainer.querySelectorAll('[data-schema-name]').length > 0
                    ? buildObjectFromFields(credentialFieldsContainer, 'cred')
                    : null;
            const hasCredentialValues =
                credential_json && Object.keys(credential_json).length > 0;

            submitBtn.disabled = true;

            try {
                if (hasCredentialValues) {
                    const credRes = await fetch(
                        '/c/exchanges/api/' + encodeURIComponent(api),
                        {
                            method: 'POST',
                            body: JSON.stringify({
                                credential_json: credential_json,
                            }),
                            headers: {
                                Accept: 'application/json',
                                'Content-Type': 'application/json',
                            },
                        }
                    );
                    if (!credRes.ok) {
                        const err = await credRes.json().catch(function () {
                            return {};
                        });
                        alert(
                            'Failed to set credentials: ' +
                                (err.message || credRes.statusText)
                        );
                        submitBtn.disabled = false;
                        return;
                    }
                }

                const createRes = await fetch('/c/exchanges', {
                    method: 'POST',
                    body: JSON.stringify({
                        api: api,
                        bank: bank,
                        api_json: api_json,
                    }),
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                });
                if (createRes.ok) {
                    apiSelect.value = '';
                    if (bankInput) bankInput.value = '';
                    onApiChange();
                    window.location.reload();
                } else {
                    const err = await createRes.json().catch(function () {
                        return {};
                    });
                    alert(
                        'Exchange create failed: ' +
                            (err.message || createRes.statusText)
                    );
                }
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
