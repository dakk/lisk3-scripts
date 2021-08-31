# Lisk3 Scripts

## lisk-saveforging.sh (corsaro and dakk)

It checks if the node forged a new block and then send new forging:status to
a telegram chat for backup.

```
pm2 start lisk-saveforging.sh
```


## lisk-nodestats.sh

Send height, finalized height and countdown to new consensus to a telegram chat.
