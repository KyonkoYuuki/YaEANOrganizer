# YaEANOrganizer
This tool to help edit ean and esk files for Xenoverse, among the features are:

* Copying animations (and associated bones) and Insert/Append/Paste them
* Change the duration of animations
* Add an offset, rotation, and scale to animations and skeletons
* Filter on what bones are allowed to be edited.
* Changing camera target focus point for cam.ean files
* Copy/delete/rename bones from EAN and ESK skeletons
* Remove keyframes from animations filtered on bones


# Credits
* Olganix and Dario for LibXenoverse of which parts were ported to Python for this

# Changelog
```
0.1.0 - Initial release
0.1.1 - Small bug fixes, Added new bone filters (thanks @Komodo), and updated section on user-defined custom bone filters
0.1.2 - Fixed duration bug when shortening duration
0.1.3 - Allow users to drag files in to open them (thanks @Seiki for the suggestion)
0.1.4 - Add EanIndex to the list for easy lookup for BAC editing
0.1.5 - Fixed loading EAN’s on the left panel using the button
0.1.6 - Add BoneIndex to the ESK list, redid SetDuration so it no longer duplicates frames
0.1.7 - Removed match duration toggle.  From now on, when pasting with a bone filter, the copied animation will have its duration adjusted to match the target animation.
0.1.8 - Added trim animation, made pasting smarter when matching durations, bug fixes with paste and set duration.  Added error dialog popup for easier debugging.
0.1.9 - Added set target camera offset to change where the camera is pointed at in cam.ean files
0.2.0 - Added the ability to copy bones from one ean to another, as well as deleting/renaming bones
0.2.1 - Added orientation to rotate animations, redid transformation options (offset, scale, & orientation)
0.3.0 - Added ESK file support, added ESK Bone Info window to edit individual bone position, rotation, and scale
0.3.1 - Numerous life improvements. Appending bones renamed to Pasting bones.  It’ll try to find existing bones to replace their data with before creating new ones.  Bone info can be copy/pasted.  Better support of bulk renaming that now allows you to do a search/replace, add prefix/suffix, or use a regex expression.
0.3.2 - Fixed trim animation not working properly, fixed animations that would have the wrong frames removed, optimized so that interpolated frames are removed before saving to reduce resulting file size
0.3.3 - Added “remove position keyframes option” to help with animation exports from certain applications that like to add position frames.
0.3.4 - Expanded “remove position keyframes” option to “remove keyframes” and allowing the user to choose what type of keyframes to remove.    
0.3.5 - EAN Bones can be added while pasting animations now.  (ESK’s still have to be edited separately)
0.3.6 - Fixed bug where pasting animations with filters can sometimes cause crashes.  Fixed bug when trying to load a second time.
0.3.7 - Optimized EAN operations so saving is faster
0.3.8 - Fixed a bug that happens when an animations has exactly 256 frames
0.3.9 - Fixed adding prefix/suffix to animation/bone names as part of renaming them
0.3.10 - Added ability to limit number of keyframes to remove
0.3.11 - Added ability to drag/associate files to exe to open them
```
