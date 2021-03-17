/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

// TODO figure out root path. For now copy your own URL gateway here
const API_ROOT = 'https://<APPID>.execute-api.us-east-1.amazonaws.com'
// TODO replace with real auth someday
const API_TOKEN = '<TOKEN>'

export async function getAPI(
    route,
    params = {},
  ) {
    const urlWithParams = new URL(`${API_ROOT}/${route}`);
    urlWithParams.searchParams.append("access_token", API_TOKEN);
    for (const [key, value] of Object.entries(params)) {
      urlWithParams.searchParams.append(key, value);
    }

    const response = await fetch(urlWithParams.toString(), {
        method: 'GET',
      });
    return response.json();
  }

export async function postAPI(
    route,
    body,
    params = {},
  ) {
    const urlWithParams = new URL(`${API_ROOT}/${route}`);
    urlWithParams.searchParams.append('access_token', API_TOKEN);

    for (const [key, value] of Object.entries(params)) {
      urlWithParams.searchParams.append(key, value);
    }
    
    const requestOptions = {
      method: 'POST',
      body: body
    }

    const response = await fetch(urlWithParams.toString(), requestOptions);
    return response.json();
  }