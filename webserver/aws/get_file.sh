SRC=$1
DEST=$2

scp -i key.pem bitnami@35.162.211.43:${SRC} ${DEST}