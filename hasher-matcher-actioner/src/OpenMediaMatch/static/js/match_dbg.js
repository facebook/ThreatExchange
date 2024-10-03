// Copyright (c) Meta Platforms, Inc. and affiliates.

var OMM = OMM || {};

OMM.match_dbg = {
    resultsById: {},

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
            img.style = "max-width: 100%;"
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
                OMM.match_dbg.resultsById[id] = data;

                if (Object.keys(OMM.match_dbg.resultsById).length === 2) {
                    OMM.match_dbg.fetchDistance(...Object.values(OMM.match_dbg.resultsById));
                }
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

    fetchDistance: (results1, results2) => {
        const body = Object.keys(results1)
            .filter(key => key in results2)
            .reduce((obj,key) =>({
                ...obj,
                [key]: [results1[key], results2[key]]
            }), {})

        fetch('/m/compare', {
            method: 'POST',
            body: JSON.stringify(body),
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                const resultsListContainer = document.getElementById("match-dbg-distance-results");
                const resultsListEntries = Object.entries(data).map(([algoName, [isMatch, details]]) => {
                    return `<tr>
                        <td>${algoName}</td>
                        <td>${isMatch ? "✅ Yes" : "❌ No"}</td>
                        <td>${details.distance}</td>
                    </tr>`
                }).join('');

                resultsListContainer.innerHTML = resultsListEntries;

                document.getElementById("match-dbg-distance-container").removeAttribute("hidden");
            })
            .catch(error => {
                console.error('Error:', error);
            });
        
    }
};