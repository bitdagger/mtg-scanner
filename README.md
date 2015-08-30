# mtg-scanner

Simple scanner for mtg. Mostly a project to get better with python and opencv 
while providing a way to keep track of my MTG collection.  

## Dependencies  
* python2  
* opencv  
* libphash  
* phash python bindings  

## Operation  

1. Run `fetch.py` to grab the images from the gatherer  
2. Run `prehash.py` to computer the image hashes for all the images  
3. Run `mtg.py` to open the camera and start matching.  

Press Enter to apply cropping and rotation, then Enter again to attempt to match.  

Press E to toggle cropping and rotation.  

Press Q to quit.  

## Notes  

There's a 180 degree rotation applied before the calculated rotation, because my camera is mounted upside down.  

This doesn't actually do much of anything yet other than spit out a multiverse ID.  

This is very much a work in progress, and not finished in any way.  

## Credits  

http://mtgjson.com for the card data  
