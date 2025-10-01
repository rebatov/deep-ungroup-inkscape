#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Ungroup extension for Inkscape 1.4+
Updated for modern Inkscape extension API
Compatible with headless mode
"""

__version__ = "1.0"  # Updated for Inkscape 1.4+

import inkex
from inkex import Transform, Style
import sys


class DeepUngroup(inkex.EffectExtension):
    """Extension to recursively ungroup groups with depth control"""

    def add_arguments(self, pars):
        """Add command line arguments"""
        pars.add_argument("--startdepth", type=int, default=0,
                         help="starting depth for ungrouping")
        pars.add_argument("--maxdepth", type=int, default=65535,
                         help="maximum ungrouping depth")
        pars.add_argument("--keepdepth", type=int, default=0,
                         help="levels of ungrouping to leave untouched")

    def _validate_arguments(self):
        """Validate command line arguments for headless compatibility"""
        if self.options.startdepth < 0:
            self.options.startdepth = 0
            inkex.errormsg("Warning: startdepth cannot be negative, set to 0")
        
        if self.options.maxdepth < 0:
            self.options.maxdepth = 65535
            inkex.errormsg("Warning: maxdepth cannot be negative, set to 65535")
        
        if self.options.keepdepth < 0:
            self.options.keepdepth = 0
            inkex.errormsg("Warning: keepdepth cannot be negative, set to 0")
            
        if self.options.startdepth > self.options.maxdepth:
            inkex.errormsg("Warning: startdepth is greater than maxdepth, no ungrouping will occur")

    def _merge_transform(self, node, transform):
        """Propagate transform to remove inheritance"""
        try:
            # Handle SVG viewBox transformation
            if node.tag.endswith('}svg') and node.get("viewBox"):
                try:
                    vx, vy, vw, vh = [float(x) for x in node.get("viewBox").split()]
                    dw = float(node.get("width", vw))
                    dh = float(node.get("height", vh))
                    viewbox_transform = Transform(
                        f"translate({-vx}, {-vy}) scale({dw / vw}, {dh / vh})")
                    this_transform = viewbox_transform @ Transform(transform)
                    this_transform = this_transform @ Transform(node.get("transform"))
                    del node.attrib["viewBox"]
                except (ValueError, TypeError, ZeroDivisionError):
                    this_transform = Transform(transform) @ Transform(node.get("transform"))
            else:
                this_transform = Transform(transform) @ Transform(node.get("transform"))

            # Set the node's transform - only set if it's not empty or identity
            transform_str = str(this_transform)
            if transform_str and transform_str != "translate(0,0)" and transform_str != "matrix(1,0,0,1,0,0)":
                node.set("transform", transform_str)
            else:
                node.pop("transform", None)
        except Exception as e:
            # Fallback: apply transform directly without modification
            # Only log in headless mode or when debugging
            if transform and str(transform) != "translate(0,0)" and str(transform) != "matrix(1,0,0,1,0,0)":
                existing_transform = node.get("transform", "")
                if existing_transform:
                    node.set("transform", f"{transform} {existing_transform}")
                else:
                    node.set("transform", str(transform))

    def _merge_style(self, node, parent_style):
        """Propagate style to remove inheritance"""
        try:
            # Parse current node's style
            current_style = Style(node.get("style", ""))
            
            # Convert node's XML style attributes to style properties and remove them
            inheritable_xml_attrs = ["fill", "stroke", "opacity", "stroke-width", "stroke-dasharray", 
                                   "stroke-linecap", "stroke-linejoin", "fill-opacity", "stroke-opacity",
                                   "font-family", "font-size", "font-weight", "font-style"]
            
            for attr in inheritable_xml_attrs:
                if node.get(attr):
                    # Node's own XML attribute takes precedence over everything
                    current_style[attr] = node.get(attr)
                    node.pop(attr, None)
            
            # Attributes that should not be propagated to children (remain local)
            non_propagated = ["filter", "mask", "clip-path"]
            local_style = Style()
            
            # Separate non-propagated attributes
            for key in non_propagated:
                if key in current_style:
                    local_style[key] = current_style[key]
                    del current_style[key]

            # Create merged style: parent styles + node's own styles (node takes precedence)
            merged_style = Style(parent_style) if parent_style else Style()
            merged_style.update(current_style)
            
            # Add back the non-propagated local styles
            merged_style.update(local_style)

            # Apply the final style to the node
            if merged_style:
                node.style = merged_style
            else:
                node.pop("style", None)
                    
        except Exception as e:
            # Fallback: preserve existing styles
            # Keep existing style as-is to avoid breaking the element
            pass

    def _merge_clippath(self, node, parent_clippath_url):
        """Handle clip-path inheritance"""
        if not parent_clippath_url:
            return

        try:
            node_transform = Transform(node.get("transform"))
            
            # Check if transform is not identity (check for meaningful transforms)
            transform_str = str(node_transform)
            if transform_str and transform_str != "translate(0,0)" and transform_str != "matrix(1,0,0,1,0,0)":
                # Create new clipPath with inverse transform
                inverse_transform = -node_transform
                
                # Ensure defs element exists
                if self.svg.defs is None:
                    self.svg.defs = inkex.etree.SubElement(self.svg, 'defs')
                
                # Create clipPath element manually
                new_clippath = inkex.etree.SubElement(
                    self.svg.defs, 'clipPath',
                    {'clipPathUnits': 'userSpaceOnUse',
                     'id': self.svg.get_unique_id("clipPath")})
                
                # Find original clippath
                original_clippath_id = parent_clippath_url[5:-1]  # Remove "url(#" and ")"
                original_clippath = self.svg.getElementById(original_clippath_id)
                
                if original_clippath is not None:
                    # Reference original clippath elements with inverse transform
                    for child in original_clippath:
                        if child.get('id'):  # Only process children with IDs
                            use_elem = inkex.etree.SubElement(
                                new_clippath, 'use',
                            {'href': f"#{child.get('id')}", 
                             'transform': str(inverse_transform),
                             'id': self.svg.get_unique_id("use")})
                    
                    parent_clippath_url = f"url(#{new_clippath.get('id')})"

            # Apply clip-path to node or chain it if node already has one
            current_clippath = node.get("clip-path")
            if current_clippath:
                # Find the end of the clip-path chain
                clippath_element = self.svg.getElementById(current_clippath[5:-1])
                while clippath_element is not None and clippath_element.get("clip-path"):
                    next_clippath_url = clippath_element.get("clip-path")
                    clippath_element = self.svg.getElementById(next_clippath_url[5:-1])
                
                if clippath_element is not None:
                    clippath_element.set("clip-path", parent_clippath_url)
            else:
                node.set("clip-path", parent_clippath_url)
        except Exception as e:
            # Fallback: apply clip-path directly
            if not node.get("clip-path"):
                node.set("clip-path", parent_clippath_url)

    def _ungroup(self, group_node):
        """Flatten a group into the same z-order as its parent"""
        try:
            parent = group_node.getparent()
            if parent is None:
                return

            parent_index = list(parent).index(group_node)
            
            # Collect group style including XML attributes that should be inherited
            group_style = Style(group_node.get("style", ""))
            
            # Add inheritable XML attributes to the style
            inheritable_attrs = ["fill", "stroke", "opacity", "stroke-width", "stroke-dasharray", 
                               "stroke-linecap", "stroke-linejoin", "fill-opacity", "stroke-opacity",
                               "font-family", "font-size", "font-weight", "font-style"]
            
            for attr in inheritable_attrs:
                attr_value = group_node.get(attr)
                if attr_value and attr not in group_style:
                    group_style[attr] = attr_value
            
            group_transform = Transform(group_node.get("transform"))
            group_clippath = group_node.get("clip-path")

            # Process children in reverse order to maintain z-order
            children = list(group_node)
            for child in reversed(children):
                try:
                    self._merge_transform(child, group_transform)
                    self._merge_style(child, group_style)
                    self._merge_clippath(child, group_clippath)
                    parent.insert(parent_index, child)
                except Exception as e:
                    # Still try to move the child to preserve structure
                    try:
                        parent.insert(parent_index, child)
                    except:
                        pass

            # Remove the now-empty group
            parent.remove(group_node)
        except Exception as e:
            # Log only critical ungroup failures
            inkex.errormsg(f"Failed to ungroup {group_node.get('id', 'unknown')}: {e}")

    def _should_ungroup(self, node, depth, height):
        """Determine if a node should be ungrouped based on criteria"""
        return (node.tag.endswith('}g') and  # SVG group element
                node.getparent() is not None and
                height >= self.options.keepdepth and
                depth >= self.options.startdepth and
                depth <= self.options.maxdepth)

    def _deep_ungroup(self, node):
        """Recursively ungroup using iteration to avoid stack limits"""
        # Use a stack-based approach instead of recursion
        stack = [{'node': node, 'depth': 0, 'prev': {'height': None}, 'height': None}]

        while stack:
            current = stack[-1]
            current_node = current['node']
            depth = current['depth']
            height = current['height']

            # Forward pass: calculate height
            if height is None:
                # Skip non-graphical elements using tag checking
                tag = current_node.tag
                if (tag.endswith('}namedview') or tag.endswith('}defs') or 
                    tag.endswith('}metadata') or tag.endswith('}foreignObject')):
                    stack.pop()
                    continue

                # Base case: not a group or empty group
                if not tag.endswith('}g') or len(current_node) == 0:
                    current['height'] = 0
                else:
                    # Recursive case: process children
                    depth += 1
                    for child in current_node:
                        stack.append({
                            'node': child, 
                            'prev': current,
                            'depth': depth, 
                            'height': None
                        })
            else:
                # Backward pass: process ungrouping
                if self._should_ungroup(current_node, depth, height):
                    self._ungroup(current_node)

                # Propagate height up
                height += 1
                previous = current['prev']
                prev_height = previous['height']
                if prev_height is None or prev_height < height:
                    previous['height'] = height

                stack.pop()

    def effect(self):
        """Main effect method"""
        try:
            # Validate arguments first
            self._validate_arguments()
            
            if self.svg.selected:
                # Process selected elements
                for element_id, element in self.svg.selected.items():
                    try:
                        self._deep_ungroup(element)
                    except Exception as e:
                        inkex.errormsg(f"Error processing selected element {element_id}: {e}")
            else:
                # Process entire document - self.svg IS the root element
                root_children = list(self.svg)
                for element in root_children:
                    try:
                        self._deep_ungroup(element)
                    except Exception as e:
                        inkex.errormsg(f"Error processing document element {element.get('id', 'unknown')}: {e}")
            
        except Exception as e:
            inkex.errormsg(f"Deep Ungroup: Critical error in main effect: {e}")
            # Re-raise to ensure Inkscape knows the extension failed
            raise


if __name__ == '__main__':
    try:
        DeepUngroup().run()
    except Exception as e:
        # Final fallback for headless mode
        print(f"Deep Ungroup Extension Error: {e}", file=sys.stderr)
        sys.exit(1)

