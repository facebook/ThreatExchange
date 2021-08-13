# Getting started with the hasher-matcher-actioner webapp

This project requires [npm](https://www.npmjs.com/get-npm) be installed. Once npm is installed, `npm install` must be run from this directory to enable usage of the scripts referenced below. (Running terraform apply will run `npm install` for you.)

To run, build or test you need a .env file in this directory. One is created for you when you terraform apply, and it should look like .env.example.

To sign in (whether running from localhost, the s3 bucket url, or the cloudfront distribution) you need a user. Take these steps to create a user after you've run terraform apply:

1. Open Your User Pools in the AWS console (e.g., https://console.aws.amazon.com/cognito/users/?region=us-east-1 substituting your region as appropriate)
2. Select the user pool configured for your HMA environment.
3. Select Users and groups (left nav).
4. Select Create user and follow the instructions. You can leave Phone Number blank, if you wish; Username, Temporary password and Email are required. Leaving Mark email as verified checked speeds things up by skipping the built-in email verification step.

By default, the Cognito user pool app client configuration uses identity and access tokens that are valid for 60 minutes, and a refresh token that's valid for 30 days. Those settings can be changed via the AWS console once your environment is created using terraform, or you can change values in `/terraform/authentication/main.tf`.

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

### Running the Webapp Locally

Even when running the UI locally, the API will need to serve from a full instance of HMA. Follow the [Hasher-Matcher-Actioner README](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/README.md) for details on how to spin up an instance.

After deploying an instance, build and then start your instance locally. It may take a few refreshes, but you should be directed to the same login page as the one as the instance you deployed. If you haven't set up an account yet, see the note on how to do that in the [Hasher-Matcher-Actioner README](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/README.md).

Once you have done that, the pages you are served should match your local copy, and you can develop on the UI.

### Lint and Formatting

It also utilizes [eslint](https://eslint.org/) and [prettier](https://prettier.io/) configured in [.eslintrc.json](.eslintrc.json) and [.prettierrc.json](.prettierrc.json) respectively. (Both tools have code editor [integrations](https://prettier.io/docs/en/editors.html) that may be found helpful.)

Please run the following checks/formating before submitting a PR.

```
# linter
npx eslint src --ext .js,.jsx,.tsx,.ts --fix
# formatter
npx prettier --write src
# ensure app builds
npm run build
```

# Deploying to S3

Terraform takes care of most of it. But it is not smart enough to do the deploy. It must be instructed to do so. Use the terraform taint command as outlined below.

Run these in the `hasher-matcher-actioner` directory.

```shell
$ terraform -chdir=terraform taint "null_resource.build_and_deploy_webapp"
$ terraform -chdir=terraform apply -var prefix="$(whoami)"
```

You might need to force refresh your browser for the changes to take effect. S3 sends liberal caching headers. `<Cmd>+<Shift>+R` on Firefox and potentially other browsers.
