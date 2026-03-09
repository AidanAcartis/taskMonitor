#!/bin/bash

# Obtenir la date du jour au format YYYY-MM-DD
today=$(date "+%Y-%m-%d")

# Filtrer l'historique des commandes et afficher celles du jour
grep "^$today" ~/.bash_history
