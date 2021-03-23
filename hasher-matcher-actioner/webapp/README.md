# Getting started with the hasher-matcher-actioner webapp

This project requires [npm](https://www.npmjs.com/get-npm) be installed. Once installed `npm install` from within this directory should enable usage of the scripts referenced below.

To run, build or test you need to create a .env file in the webapp directory. One is created for you when you terraform apply, and it should look something like what you see in .env.example.

To sign in (whether running from localhost, the s3 bucket url, or the cloudfront distribution) you need a user. Take these steps to create a user after you've run terraform apply:

1. Open Your User Pools in the AWS console (e.g., https://console.aws.amazon.com/cognito/users/?region=us-east-1)
2. Select the user pool configured for your HMA environment.
3. Select Users and groups (left nav).
4. Select Create user and follow the instructions. You can leave Phone Number blank, if you wish; Username, Temporary password and Email are required. Leaving Mark email as verified checked speeds things up by skipping the built-in email verification step.

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
