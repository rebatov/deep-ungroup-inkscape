# Deep Ungroup Extension for Inkscape 1.4+

This is an updated version of the Deep Ungroup extension that works with Inkscape 1.4 and higher. The extension allows you to recursively ungroup all groups in selected objects or the entire document, with fine-grained control over the ungrouping depth.

## Features

- **Recursive ungrouping**: Ungroups nested groups to any desired depth
- **Depth control**: Set starting depth, maximum depth, and levels to keep from bottom
- **Selection support**: Works on selected objects or entire document if nothing is selected
- **Modern API**: Updated to use Inkscape 1.4+ extension API
- **Preserve attributes**: Properly merges transforms, styles, and clip-paths when ungrouping

## Installation

1. **Find your Inkscape extensions directory:**
   - **Linux**: `~/.config/inkscape/extensions/`
   - **Windows**: `C:\Users\[username]\AppData\Roaming\inkscape\extensions\`
   - **macOS**: `~/.config/inkscape/extensions/` or `/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions/`

2. **Copy the extension files:**
   - Copy `ungroup_deep.py` to the extensions directory
   - Copy `ungroup_deep.inx` to the extensions directory

3. **Restart Inkscape** if it was running

## Usage

### GUI Usage

1. **Access the extension:**
   - Go to `Extensions` → `Arrange` → `Deep Ungroup`

2. **Configure options:**
   - **Starting Depth**: The minimum depth level where ungrouping begins (default: 0)
   - **Stopping Depth (from top)**: The maximum depth level for ungrouping (default: 65535)
   - **Depth to Keep (from bottom)**: Number of group levels to preserve at the bottom (default: 0)

3. **Run the extension:**
   - Select objects to ungroup (or leave nothing selected to process entire document)
   - Click `Apply`

### Command Line Usage

You can use this extension from the command line with Inkscape 1.4+:

#### Basic Usage
```bash
# Process entire document with default settings
inkscape --actions="org.inkscape.deep-ungroup" input.svg \
         --export-filename=output.svg --export-type=svg

# Process with selection and additional operations
inkscape --actions="select-all;org.inkscape.deep-ungroup;export-filename:output.svg;export-do" input.svg
```

#### Batch Processing
```bash
# Process multiple files
for file in *.svg; do
  inkscape --actions="org.inkscape.deep-ungroup" "$file" \
           --export-overwrite --export-type=svg
done

# Or using find for recursive processing
find /path/to/svg/files -name "*.svg" -exec \
  inkscape --actions="org.inkscape.deep-ungroup" {} \
           --export-overwrite --export-type=svg \;
```

#### Combined Operations
```bash
# Ungroup and flatten paths in one command
inkscape --actions="select-all;org.inkscape.deep-ungroup;select-all;path-flatten;export-filename:output.svg;export-do" input.svg
```

#### Verification
To check if your extension is available:
```bash
# List all actions (should include your extension after installation)
inkscape --action-list | grep ungroup
```

## Parameters Explained

- **Starting Depth (0)**: Begin ungrouping at this depth level. 0 = start immediately
- **Stopping Depth (65535)**: Stop ungrouping at this depth level from the top
- **Depth to Keep (0)**: Preserve this many group levels at the deepest level

### Example Scenarios

**Scenario 1: Complete ungrouping**
- Starting Depth: 0
- Stopping Depth: 65535  
- Depth to Keep: 0
- Result: All groups are ungrouped

**Scenario 2: Keep outermost groups**
- Starting Depth: 1
- Stopping Depth: 65535
- Depth to Keep: 0  
- Result: Top-level groups remain, but their contents are ungrouped

**Scenario 3: Preserve innermost groups**
- Starting Depth: 0
- Stopping Depth: 65535
- Depth to Keep: 1
- Result: All groups are ungrouped except the deepest level

## Changes from Original Version

This updated version includes several improvements for Inkscape 1.4+ compatibility:

### Technical Changes
- **Modern Extension API**: Uses `inkex.EffectExtension` instead of deprecated `inkex.Effect`
- **New Argument Parsing**: Uses `add_arguments()` instead of `OptionParser`
- **Updated Transform Handling**: Uses modern `inkex.Transform` class with `@` operator
- **Modern Style Management**: Uses `inkex.Style` class for CSS style handling
- **Tag-based Element Handling**: Uses robust tag checking instead of specific element classes
- **Improved Error Handling**: Better compatibility with different Inkscape versions
- **Python 3 Compatibility**: Updated for Python 3 syntax and best practices
- **Command Line Support**: Works reliably from command line with proper action ID

### INX File Updates
- **Modern XML Schema**: Updated to current Inkscape extension format
- **Namespace Declaration**: Proper xmlns declaration
- **Parameter Syntax**: Updated parameter syntax (`gui-text` instead of `_gui-text`)
- **Menu Structure**: Updated menu structure syntax
- **Unique Extension ID**: Uses `org.inkscape.deep-ungroup` to avoid conflicts

### Dependencies Removed
- **No NumPy Dependency**: Removed dependency on numpy.matrix
- **No Legacy Modules**: Removed dependencies on deprecated `simplestyle`, `simpletransform`

## Compatibility

- **Inkscape Version**: 1.4 and higher
- **Python Version**: Python 3.6+
- **Operating Systems**: Linux, Windows, macOS

## Troubleshooting

**Extension not appearing in menu:**
- Ensure both `.py` and `.inx` files are in the correct extensions directory
- Restart Inkscape completely
- Check Inkscape's error console (Help → About Extensions) for error messages

**Python errors:**
- Ensure you have Python 3 installed
- The extension uses only standard library modules, so no additional Python packages are required

**Command line usage not working:**
- Ensure Inkscape 1.4+ is installed (check with `inkscape --version`)
- Verify the extension is properly installed by running it through the GUI first
- Check if the extension appears in the action list: `inkscape --action-list | grep ungroup`
- Use absolute paths for input/output files if having issues
- Extension ID is: `org.inkscape.deep-ungroup`

**Extension not in action list:**
- Install the extension files in the correct directory (see Installation section)
- Restart Inkscape completely
- Test the extension through the GUI (Extensions → Arrange → Deep Ungroup)
- The extension should appear in `--action-list` after successful GUI installation

**Parameter limitations:**
- Inkscape 1.4+ command line has limited support for passing custom parameters to extensions
- For custom parameters (startdepth, maxdepth, keepdepth), use the GUI interface
- Command line usage applies the extension with default parameter values from the .inx file
- To change defaults, you can modify the default values in the `.inx` file