// Copyright (c) Meta Platforms, Inc. and affiliates.

// Import hash wasm library for generating MD5 hash.
import { createMD5 } from '../node_modules/hash-wasm/dist/index.esm.min.js';
//import the library to talk to imagemagick
import * as Magick from '../node_modules/wasm-imagemagick/dist/magickApi.js';

let getPDQHash = "";
let hasher = null;

/**
 * This method is used for generating PDQ / MD5 hashes based on the type of file i.e. Image /Video.
 * @param {*} data 
 * @param {*} fname 
 * @param {*} tempfname 
 * @param {*} isImageFile 
 * @param {*} isVideoFile 
 */
export async function getPDQMD5Hash(data, fname, tempfname, isImageFile, isVideoFile, dataArray) {
	// Save the selected files to emscripten file system for c++ code to access the file.
	let stream = FS.open(fname, 'w+');
	FS.write(stream, data, 0, data.length, 0);
	FS.close(stream);

	let hashResult = "";
	if (isImageFile) {
		// Call the function for converting the image to .pnm file using image magick web assembly.
		hashResult = await getPDQHash(fname, tempfname);
	}
	else if (isVideoFile) {
		// Call the function for generating MD5 hash of video file.
		hashResult = await getMD5Hash(dataArray);
	}
	else {
		hashResult = "";
	}
	return hashResult;
}

// This method is used for generating the PDQ hash in webbrowser by calling wasm method.
getPDQHash = async function (filename, tempfilename) {

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
	// return back the result.
	return result;
};

/**
 * The below method is used for generating the MD5 hash of the video file .
 * @param {*} file 
 * @returns 
 */
const getMD5Hash = async (dataArray) => {
	if (hasher) {
		hasher.init();
	} else {
		hasher = await createMD5();
	}

	for (let count = 0; count < dataArray.length; count++) {
		hasher.update(dataArray[count]);
	}

	const hash = hasher.digest();
	return Promise.resolve(hash);
};
