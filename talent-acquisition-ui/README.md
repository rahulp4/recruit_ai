

  npm install -g serve
  serve -s build
  






CONFIGUTE DEVELOPMENT AND PRODUCTION

1. CHANGE in .env

REACT_APP_API_BASE_URL=http://127.0.0.1:5000/api - DEV
#REACT_APP_API_BASE_URL=https://api.hyreassist.co/api - PRODU

2. Add "proxy": "http://localhost:8000",  to package.json

3. apiService.ts
//PRODUCTION
// const API_BASE_URL = 'https://api.hyreassist.co/api';

//DEVELOPMENT
const API_BASE_URL = '/api'; // <<<<< CHANGE THIS TO A RELATIVE PATH









# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

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

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).


# FIREBASE
npm install firebase
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyB6dG7sEKtI-NQO_k3-AZSSLXq-nJMzSEk",
  authDomain: "profileauth-90a2f.firebaseapp.com",
  projectId: "profileauth-90a2f",
  storageBucket: "profileauth-90a2f.firebasestorage.app",
  messagingSenderId: "449144548740",
  appId: "1:449144548740:web:62f4ed418007908ec081d1"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);


PYTHON SERVICE ACCOUNT
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)




# BRANDING
You are an expert in building brand names in today's world. You can suggest some of the best names for new application considering this is an era
where AI beased applications are taking over.

Please help me to name an application which will be a SaaS service.
Features are as follows

1. It can help the talent acquisition team in HR to acquire profiles and sort them as per given job decription.
2. It can assign scores to resumes against the goven job decription, say there is job decription and we receive 1000 profiles,
it can give score to each profile based on multiple criteria in job description, organization policies. THis is all AI based and leverage some of the
state of the art techniques in AI to to this.
3. This save lot time.
4. Talent and HR can see the listed profiles and schedule . Scheuling can be automated as well.
5. There are many more such functions which will be part of this application and offering.
6. We woudl leverage AI for most of the features to build futurestic application

Please suggest Name of applicatoin/offering which whould be used with application and on the online service portal.
Punch line to be used. Any other suggestions.

# JD Rules
ok now can you suggest, json template for job description along with
1. Rule in each section
2. Each section to have mandatory or optional.
3. Each section to have weightage, from 0 to 5. 5 being max
4. In case of rule where years/months ranage are required, weightage will help to caculate the score later
5. In case of descriptive needs, the match percentage will help to caculate score on the scale of weightage
6. In case where we say a particular requirement is in negative, like number of switches in last 5 years should not be more then 2 or 1, and if the outcome
is against this, the score will be ne negative.
7. Scores will be on scale from 0 to 100 percent. If the outcome is againts then this score will be in range from 0 to negative percentage depdending upon
deviatioins.
8. I hope engine that we will develop for cacluating score can work on outcome of vector search and similarity outcome.

First give me well thought sctructure for JSON , we will review and improve it further if above are possible.