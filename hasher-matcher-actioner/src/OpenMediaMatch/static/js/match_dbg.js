// Copyright (c) Meta Platforms, Inc. and affiliates.

var OMM = OMM || {};

OMM.match_dbg = {
    onFileChange: (id) => {
        const form = document.getElementById(id + "-file-upload");
        const container = document.getElementById(id + "-img");
        const dest_div = document.getElementById(id + "-signals");

        if (!('files' in form) || form.files.length !== 1) {
            return;
        }
        dest_div.replaceChildren([]);
        const formData = new FormData();
        const file = form.files[0];
        formData.append("photo", file);

        const reader = new FileReader();
        reader.onload = () => {
            const imgUrl = reader.result;
            const img = new Image();
            img.src = imgUrl;
            img.style = "max-width: 180px; max-height: 180px;"
            container.replaceChildren(img);
        };
        reader.readAsDataURL(file);

        fetch('/h/hash', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                // Handle the response from the server here
                OMM.match_dbg.renderHashResult(id, data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    },
    renderHashResult: (id, result) => {
        const dest_div = document.getElementById(id + "-signals");

        const signalList = Object.entries(result).map(([signal_type, val]) => {
            const text = `${signal_type}: ${val}`;
            return `<li><div class="text-truncate" style="cursor: pointer;" data-toggle="tooltip" title="copy to clipboard ${val}" onclick="navigator.clipboard.writeText('${val}')">
            ${text}
          </div></li>`

        }).join('');
        const signalHTML = `
              <h4>Signal Types</h4>
              <ul>${signalList}</ul>
          `;
        dest_div.innerHTML = signalHTML;
    },
    copyHash: (id, hash_text) => {
        const src = document.getElementById(id);
        navigator.clipboard.writeText(hash_text)
        src.toolti
    },
};