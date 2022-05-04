// Import hash wasm library for generating MD5 hash.
import { createMD5} from '../node_modules/hash-wasm/dist/index.esm.min.js';
//import the library to talk to imagemagick
import * as Magick from '../node_modules/wasm-imagemagick/dist/magickApi.js';

let DoMagickCall = "";
// Execute the following codes once the DOM contents are loaded completely.
document.addEventListener("DOMContentLoaded", (event) => {
	const chunkSize = 64 * 1024 * 1024;
	const fileReader = new FileReader();
	let hasher = null;

	function hashChunk(chunk) {
		return new Promise((resolve, reject) => {
			fileReader.onload = async (e) => {
				const view = new Uint8Array(e.target.result);
				hasher.update(view);
				resolve();
			};

			fileReader.readAsArrayBuffer(chunk);
		});
	}

	const readFile = async (file) => {
		if (hasher) {
			hasher.init();
		} else {
			hasher = await createMD5();
		}

		const chunkNumber = Math.floor(file.size / chunkSize);

		for (let i = 0; i <= chunkNumber; i++) {
			const chunk = file.slice(
				chunkSize * i,
				Math.min(chunkSize * (i + 1), file.size)
			);
			await hashChunk(chunk);
		}

		const hash = hasher.digest();
		return Promise.resolve(hash);
	};

	document.getElementById("uploadFiles").onclick = function () {
		document.getElementById("uploadFiles").classList.add("upload--loading");
		document.getElementsByClassName("upload-hidden")[0].click();
	}


	document.getElementById("myfile").onchange = function () {
		let files = document.getElementById("myfile").files;

		document.getElementById("uploadFiles").classList.remove("upload--loading");
		document.getElementsByTagName("BODY")[0].classList.add('file-process-open');
		// Loop through the selected files files.
		for (let i = 0; i < files.length; i++) {
			let fname = '';
			let tempfname = '';
			let reader = new FileReader();

			let file = files.item(i);
			if (file) {
				fname = file.name;
				if (fname) {
					tempfname = `${fname.substr(0, fname.lastIndexOf("."))}_temp.pnm`;
				}
			}

			reader.onloadend = async function (e) {

				let result = reader.result;
				const data = new Uint8Array(result);

				// Save the selected files to emscripten file system for c++ code to access the file.
				let stream = FS.open(fname, 'w+');
				FS.write(stream, data, 0, data.length, 0);
				FS.close(stream);

				let isImageFile = file.type.includes("image");
				const isVideoFile = file.type.includes("video");

				document.getElementById("resHeader").style.display = "block";
				if (isImageFile) {
					// Call the function for converting the image to .pnm file using image magick web assembly.
					DoMagickCall(fname, tempfname, formatFileSize(file.size, 2));
				}
				else if (isVideoFile) {
					// Generate a new table row and cell contents and append to result table .
					const resultTable = document.getElementById('resBody').insertRow(-1);
					if (resultTable) {
						const cellOne = resultTable.insertCell(0);
						const cellTwo = resultTable.insertCell(1);
						const cellThree = resultTable.insertCell(2);
						cellOne.innerHTML = fname;
						cellTwo.innerHTML = await readFile(file);
						cellThree.innerHTML = formatFileSize(file.size, 2);
					}
				}
				else {
					const resultTable = document.getElementById('resBody').insertRow(-1);
					if (resultTable) {
						const cellOne = resultTable.insertCell(0);
						cellOne.colSpan = "3";
						cellOne.innerHTML = `File ${fname} cannot be processed.Please ensure only Image/Video files are only selected for calculating file Hash.`;
					}
				}

			}

			reader.readAsArrayBuffer(file);
		}
	}
});

// Fetch the image to rotate, and call image magick
DoMagickCall = async function (filename, tempfilename, filesize) {

	// Read the file whose hash needs to be calculated.     
	let sourceBytes = FS.readFile(filename);

	// Call image magick with one source image, and command to convert the file to .pnm file required for hash calculation.
	const files = [{ 'name': filename, 'content': sourceBytes }];
	const command = ["convert", filename, "-density", "400x400", tempfilename];

	let processedFiles = await Magick.Call(files, command);

	// Response can be multiple files (example split)
	// here we know we just have one
	let firstOutputImage = processedFiles[0];

	const data = new Uint8Array(await firstOutputImage['blob'].arrayBuffer());

	let stream = FS.open(tempfilename, 'w+');
	FS.write(stream, data, 0, data.length, 0);
	FS.close(stream);

	var result = Module.ccall(
		'getHash',	// name of C function
		'string',	// return type
		['string'],	// argument types
		[filename]	// arguments
	);

	// Remove the file so that we can free some memory.
	FS.unlink(filename);
	document.getElementById("resHeader").style.display = "block";

	// Generate a new table row and cell contents and append to result table .
	const resultTable = document.getElementById('resBody').insertRow(-1);
	if (resultTable) {
		const cellOne = resultTable.insertCell(0);
		const cellTwo = resultTable.insertCell(1);
		const cellThree = resultTable.insertCell(2);
		cellOne.innerHTML = filename;
		cellTwo.innerHTML = result;
		cellThree.innerHTML = filesize;
	}
};

/**
Method for getting the file size.
**/
function formatFileSize(bytes, decimalPoint) {
	if (bytes == 0) return '0 Bytes';
	var k = 1024,
		dm = decimalPoint || 2,
		sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
		i = Math.floor(Math.log(bytes) / Math.log(k));
	return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}