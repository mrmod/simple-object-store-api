#!/bin/bash

uvicorn main:api --reload &

uvicorn main:s3 --reload 