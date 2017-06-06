#! /usr/bin/env bash
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
