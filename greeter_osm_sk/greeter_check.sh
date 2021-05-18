#!/bin/bash
# set -x
set -u
# print a warning if there wasn't any new welcome message for the last 2 weeks
threshold_days=14
rcfile=.greeterrc
verbose=0

if [ ! -f "${rcfile}" ]
then
  echo "Rc file (${rcfile}) could not be found in the current directory!"
  exit 1
fi

username=$(awk -F= '$1 == "username"{print $2}' "${rcfile}")
password=$(awk -F= '$1 == "password"{print $2}' "${rcfile}")

if [ -z "${username}" -o -z "${password}" ]
then
  echo "Neither username nor password may be empty!"
  exit 1
fi

page=$(curl -c cookies -s https://www.openstreetmap.org/)
token=$(echo "${page}" | sed -n '/csrf-token/s%.*content="\([^"]*\)".*%\1%p')

if [ -z "${token}" ]
then
  echo "Fatal! Token may not be empty!"
  exit 1
fi

[ "${verbose}" -eq 1 ] && echo "token1: ${token}"

page=$(curl -Ls -b cookies -c cookies -F username="${username}" \
	                              -F password="${password}" \
				      -F 'authenticity_token='${token} \
				      https://www.openstreetmap.org/login)
token=$(echo "${page}" | sed -n '/csrf-token/s%.*content="\([^"]*\)".*%\1%p')

[ "${verbose}" -eq 1 ] && echo "token2: ${token}"

last_sent=$(curl -s -b cookies https://www.openstreetmap.org/messages/outbox | \
	    awk '/inbox-subject.*Privitanie/{getline; print}' | \
	    sed -n '/inbox-sent/{s%<[^>]*>%%g;p; q;}' | \
	    awk '{print $1, $2, $3, $5, $6}')

if [ -z "${last_sent}" ]
then
  echo "Error! Time of the last message sent could not be read! (check username/password)"
  exit 1
fi

last_timestamp=$(date +"%s" -d "${last_sent}")
now_timestamp=$(date '+%s')
difference_hours=$(((now_timestamp-last_timestamp)/3600))
difference_days=$(((now_timestamp-last_timestamp)/86400))

[ "${verbose}" -eq 1 ] && {
  echo "last_timestamp: ${last_timestamp}"
  echo "now_timestamp: ${now_timestamp}"
  echo "last message was sent ${difference_days} days (or ${difference_hours} hours) ago"
}

if [ "${difference_days}" -gt "${threshold_days}" ]
then
  echo "Warning! No new message was sent for the last ${threshold_days} days"
  exit 1
fi

exit 0
