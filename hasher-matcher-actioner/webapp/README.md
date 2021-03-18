# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# Getting started with the hasher-matcher-actioner webapp

This project requires [npm](https://www.npmjs.com/get-npm) be installed. Once installed  `npm install` from within this directory should enable usage of the scripts referenced below.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.

## Contributing 

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

It also utilizes [eslint](https://eslint.org/) and [prettier](https://prettier.io/) configured in [.eslintrc.json](.eslintrc.json) and [.prettierrc.json](.prettierrc.json) respectively. (Both tools have code editor [integrations](https://prettier.io/docs/en/editors.html) that may be found helpful.) 

Please run the following checks/formating before submitting a PR.

```
# linter
npx eslint src --ext .js,.jsx --fix
# formatter
npx prettier --write src
# ensure app builds
npm run build 
```
