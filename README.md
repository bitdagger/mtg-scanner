# mtg-scanner

Simple scanner for mtg. Mostly a project to get better with python and opencv 
while providing a way to keep track of my MTG collection.  

## Dependencies  
* python2  
* opencv  
* libphash  
* phash python bindings  
* imagemagick  

## Operation  

1. Run `mtg-scanner --update` to grab the images from the gatherer and calculate hashes  
2. Run `mtg-scanner --scan` to open the camera and start scanning
3. Run `mtg-scanner --export` to export a list of cards in your collection

## Optional Arguments  
* `--debug` - Enable debugging when scanning  
* `--camera <integer>` - Specify a camera ID to use for scanning  
* `--database <DB>` - Specify a database name to use when scanning and exporting  

### While Scanning  

The stand-by screen has a blue border around it. From the stand-by screen, 
press Enter to isolate the card. If the framing is good, then press enter again 
to attempt to match. If the framing is not good, then you can press ESC or 
Backspace to go back to the stand-by screen.  

Once a match has been found it will display the matched card on the screen. 
Press Enter to add the card to your collection. If the card is a foil you can 
press F instead of Enter to add the card to your collection and mark it as a 
foil. If the card displayed is not the desired card, press N to try again. You 
can also press ESC to go back to the stand-by screen.

If you have multiple copies you want to add, after adding the first card you 
can press the + key on the numpad to bring up the confirmation prompt again. As 
before you can press Enter to add the card, F to add a foil, or ESC or 
Backspace to go back to the stand-by screen. You can press P instead of enter 
when adding a card to add a playset of that card instead (adds 4 copies at once).

Press Q at any time to quit.  

## Why Python2 and not Python3?  

I originally wrote the scanning system for python 2. After everything was fully 
functional I tried to upgrade everything to python 3, but the opencv library that 
is required for the scanning process does not support python 3. As such, until 
opencv supports python 3, this code will stay on python 2.  

## Credits  

http://mtgjson.com for the card data  
