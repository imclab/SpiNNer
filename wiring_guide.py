#!/usr/bin/env python

"""
A tool which generates LaTeX/TikZ wiring guides.

This almighty python script, approximately speaking first generates data
structures containing the information to be presented and then proceeds to
generate an absolutely massive LaTeX file.
"""

from collections import defaultdict

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

from model import topology
from model import cabinet
from model import board
from model import transforms
from model import metrics
from model import coordinates

import diagram

################################################################################
# Load Parameters
################################################################################

from params_physical import *

#from params_spin103 import *
#from params_spin104 import *
#from params_spin105 import *
from params_spin106 import *

# XXX
show_wiring_metrics = False
show_topology_metrics = False
show_development = False
show_board_position_list = False
show_wiring_instructions = False
show_wiring_patterns = True


################################################################################
# Generate models
################################################################################

# Set up the cabinet data structure
cabinet_system = cabinet.System(
	cabinet = cabinet.Cabinet(
		rack = cabinet.Rack(
			slot = cabinet.Slot(
				dimensions    = (slot_width, slot_height, slot_depth),
				wire_position = wire_positions,
			),
			dimensions   = (rack_width, rack_height, rack_depth),
			num_slots    = num_slots_per_rack,
			slot_spacing = slot_spacing,
			slot_offset  = slot_offset,
		),
		dimensions   = (cabinet_width, cabinet_height, cabinet_depth),
		num_racks    = num_racks_per_cabinet,
		rack_spacing = rack_spacing,
		rack_offset  = rack_offset,
	),
	num_cabinets    = num_cabinets,
	cabinet_spacing = cabinet_spacing,
)

# Create an inter-linked torus
torus = board.create_torus(width, height)

# Convert to Cartesian coordinates as the coming manipulations use/abuse this
cart_torus = transforms.hex_to_cartesian(torus)

# Cut the left-hand side of the torus off and move it to the right to form a
# rectangle
rect_torus = transforms.rhombus_to_rect(cart_torus)

# Compress the coordinates to eliminate the "wavy" pattern on the y-axis turning
# the board coordinates into a continuous mesh.
comp_torus = transforms.compress(rect_torus, 1 if compress_rows else 2
                                           , 2 if compress_rows else 1
                                           )

# Show where the folds will occur
fold_spaced_torus = transforms.space_folds(comp_torus, (num_folds_x, num_folds_y))

# Actually do the folds
folded_torus = transforms.fold(comp_torus, (num_folds_x, num_folds_y))

# Place spaces in the folded version to see how it folded
folded_spaced_torus = transforms.space_folds(folded_torus, (num_folds_x, num_folds_y))

# Place spaces where the design is split into racks & cabinets
folded_cabinet_spaced_torus = transforms.space_folds(folded_torus, (num_cabinets, num_racks_per_cabinet))

# Map to cabinets
cabinet_torus = transforms.cabinetise( folded_torus
                                     , num_cabinets
                                     , num_racks_per_cabinet
                                     , num_slots_per_rack
                                     )

# Map to physical space for the cabinets described
phys_torus = transforms.cabinet_to_physical(cabinet_torus, cabinet_system)


 ##############################################################################
################################################################################
# Generate Figures
################################################################################
 ##############################################################################

################################################################################
# Useful Definitions
################################################################################

# Human-readable names for direction constants
DIRECTION_NAMES = {
	NORTH      : "North",
	NORTH_EAST : "North East",
	EAST       : "East",
	SOUTH      : "South",
	SOUTH_WEST : "South West",
	WEST       : "West",
}

# Mapping of directions to colours for the principle wiring directions
DIRECTION_COLOURS = [(NORTH,"red"),(EAST,"green"),(SOUTH_WEST,"blue")]

# A key describing the colours used in diagrams
colour_key = ", ".join(r"{\color{%s}%s}"%(c, DIRECTION_NAMES[d])
                       for (d,c) in DIRECTION_COLOURS)

# Display coordinates for Cartesian positions
board2coord = dict(cart_torus)

# Given a Cartesian coordinate, get a board.
cart_coord2board = dict((c,b) for (b,c) in cart_torus)


def generate_diagram(boards, b2l, add_board_func,
                    show_wires = True,
                    cabinet_system = None, cabinet_scale = 1.0):
	"""
	Generates a diagram using the board positions shown and the mapping from board
	to coordinate to use as a label.
	"""
	
	d = diagram.Diagram()
	
	d.set_cabinet_system(cabinet_system, cabinet_scale)
	
	for board, coord in boards:
		# Add board
		add_board_func(d, board, coord)
		if cabinet_system is not None:
			d.add_label(board, r"\tiny %d,%d"%(b2l[board]), ["rotate=90"])
		else:
			d.add_label(board, r"\tiny %d,%d"%(b2l[board]))
		
		# Add wires
		if show_wires:
			for direction, colour in DIRECTION_COLOURS:
				d.add_wire(board, direction, ["thick",colour])
	
	return d

################################################################################
# Basic Torus Diagram
################################################################################

# Show the regular torus with its wiring
torus_diagram = generate_diagram( cart_torus
                                , board2coord
                                , diagram.Diagram.add_board_hexagon
                                )
torus_diagram_tikz = torus_diagram.get_tikz()

# Add a line to indicate where it will be chopped
bottom_left = torus_diagram.get_tikz_ref(cart_coord2board[(0,0)], SOUTH_WEST)
max_y = max((y for (x,y) in cart_coord2board if x == 0))
top_left = torus_diagram.get_tikz_ref(cart_coord2board[(0,max_y)], WEST)

torus_diagram_tikz += r"""
\draw ([yshift=-0.5cm]%(bottom_left)s) -- ([yshift=1cm]%(top_left)s) [dashed,ultra thick];
"""%{
	"bottom_left":bottom_left,
	"top_left":top_left,
}


################################################################################
# Rectangular Torus Diagram
################################################################################

# Show after wrapping into a rectangle
rect_torus_diagram_tikz = generate_diagram( rect_torus
                                          , board2coord
                                          , diagram.Diagram.add_board_hexagon
                                          ).get_tikz()

# Show after compressing it into a regular grid
comp_torus_diagram_tikz = generate_diagram( comp_torus
                                          , board2coord
                                          , diagram.Diagram.add_board_square
                                          ).get_tikz()

################################################################################
# Folded Torus Diagram
################################################################################

# Show with spaces for folds
fold_spaced_torus_diagram_tikz = generate_diagram( fold_spaced_torus
                                                 , board2coord
                                                 , diagram.Diagram.add_board_square
                                                 , show_wires = False
                                                 ).get_tikz()

# Show folded diagram
folded_torus_diagram_tikz = generate_diagram( folded_cabinet_spaced_torus
                                            , board2coord
                                            , diagram.Diagram.add_board_square
                                            ).get_tikz()


################################################################################
# Cabinetised Torus Diagram
################################################################################

cabinet_torus_diagram_tikz = generate_diagram( cabinet_torus
                                             , board2coord
                                             , diagram.Diagram.add_board_cabinet
                                             , cabinet_system = cabinet_system
                                             , cabinet_scale = cabinet_diagram_scaling_factor,
                                             ).get_tikz()


################################################################################
# Topology Metrics
################################################################################

width_boards  = max(x for (c,(x,y)) in comp_torus) + 1
height_boards = max(y for (c,(x,y)) in comp_torus) + 1


def generate_wiring_loop(boards, direction, diagram, start = (0,0,0)):
	c2b = dict((c,b) for (b,c) in boards)
	start_board = c2b[start]
	loop = list(board.follow_wiring_loop(start_board, direction))
	
	style = ["thick", dict(DIRECTION_COLOURS)[direction]]
	
	for b in loop:
		diagram.add_wire( b
		                , direction
		                , style
		                )
		diagram.add_packet_path( b
		                       , direction
		                       , topology.opposite(direction)
		                       , ["dashed"] + style
		                       )
	
	return len(loop)


def generate_packet_loop(boards, direction, diagram, start = (0,0,0)):
	c2b = dict((c,b) for (b,c) in boards)
	start_board = c2b[start]
	loop = list(board.follow_packet_loop( start_board
	                                    , topology.opposite(direction)
	                                    , direction
	                                    ))
	style = ["thick", dict(DIRECTION_COLOURS)[direction]]
	
	for in_direction, b in loop:
		diagram.add_packet_path( b
		                       , in_direction
		                       , topology.opposite(b.follow_packet(in_direction, direction)[0])
		                       , ["dashed"] + style
		                       )
		diagram.add_wire( b
		                , in_direction
		                , style
		                )
	
	# Number of boards crossed is (threeboards_crossed*3)/2 and the number of
	# nodes crossed is 4 times this (see Simon's document).
	return ((len(loop)*3)/2) * 4


d = generate_diagram( torus
                    , board2coord
                    , diagram.Diagram.add_board_hexagon
                    , show_wires = False
                    )

wiring_loop_north_length      = generate_wiring_loop(torus, NORTH, d)
wiring_loop_east_length       = generate_wiring_loop(torus, EAST, d)
wiring_loop_south_west_length = generate_wiring_loop(torus, SOUTH_WEST, d)

wiring_loop_diagram_tikz = d.get_tikz()

d = generate_diagram( torus
                    , board2coord
                    , diagram.Diagram.add_board_hexagon
                    , show_wires = False
                    )

packet_loop_north_length      = generate_packet_loop(torus, NORTH,      d, (0,1,0))
packet_loop_east_length       = generate_packet_loop(torus, EAST,       d, (1,1,0))
packet_loop_south_west_length = generate_packet_loop(torus, SOUTH_WEST, d, (0,0,0))

packet_loop_diagram_tikz = d.get_tikz()


################################################################################
# Wiring Stats For Cabinets
################################################################################

def calculate_wire_cabinet_stats(boards):
	"""
	Calculate stats about how often wires leave their own cabinet
	"""
	# Counters
	stats = [
		#              In-Rack  Between Racks  Between Cabinets
		(NORTH      , [0,       0,             0]),
		(EAST       , [0,       0,             0]),
		(SOUTH_WEST , [0,       0,             0]),
	]
	
	b2c = dict(boards)
	
	for board, coord in cabinet_torus:
		for direction, counters in stats:
			source = b2c[board]
			target = b2c[board.follow_wire(direction)]
			cabinets, racks, slots = abs(target - source)
			
			if cabinets > 0:
				counters[0] += 1
			elif racks > 0:
				counters[1] += 1
			elif slots > 0:
				counters[2] += 1
			else:
				assert(False)
	
	wire_cabinet_stats = "\n".join(
		"%s & %d & %d & %d & %d \\\\"%(
			DIRECTION_NAMES[direction],
			sum(counters),
			counters[2], counters[1], counters[0],
		)
		for direction, counters in stats
	)
		
	total_wire_cabinet_stats = "Total & %d & %d & %d & %d \\\\\n"%(
			sum(sum(counters) for (d,counters) in stats),
			sum(counters[2] for (d,counters) in stats),
			sum(counters[1] for (d,counters) in stats),
			sum(counters[0] for (d,counters) in stats),
		)
	
	return wire_cabinet_stats, total_wire_cabinet_stats


wire_cabinet_stats, total_wire_cabinet_stats = calculate_wire_cabinet_stats(cabinet_torus)



################################################################################
# Wiring Length Stats
################################################################################

def calculate_wire_length_stats(boards, wire_offsets={}, num_bins = 5):
	"""
	Calculate stats about how often wires leave their own cabinet
	"""
	# Lists of wire lengths for each axis
	stats = [
		(NORTH      , []),
		(EAST       , []),
		(SOUTH_WEST , []),
	]
	
	b2c = dict(boards)
	
	for board, coord in cabinet_torus:
		for direction, lengths in stats:
			lengths.append(metrics.wire_length(boards
			                                  , board
			                                  , direction
			                                  , wire_offsets
			                                  ))
	
	# Convert stats to frequency counts
	freq_stats = []
	for direction, lengths in stats:
		hist = {}
		for length in lengths:
			hist[length] = hist.get(length,0) + 1
		
		min_len = min(hist)
		max_len = max(hist)
		bin_len = (max_len - min_len) / num_bins
		
		out_frequencies = []
		for bin_num in range(num_bins):
			bin_start = (min_len + (bin_num*bin_len)) if bin_num > 0 else 0.0
			bin_end   = min_len + (bin_num*bin_len) + bin_len
			
			out_frequencies.append((bin_start, bin_end,
			                        sum(c for (l,c) in hist.iteritems()
			                              if bin_start < l <= bin_end)))
		
		freq_stats.append((direction,
		                   sorted(out_frequencies, key=(lambda(bs,be,c):bs))))
	
	
	wire_length_stats = "\n\\midrule\n".join(
		"%s %s"%(
			DIRECTION_NAMES[direction],
			"\n".join(
				"&$%.2f < l \\le %.2f$&%d\\\\\n"%(bin_start, bin_end, count)
				for (bin_start, bin_end, count) in freq_counts
			)
		)
		for (direction, freq_counts) in freq_stats
	)
	
	return wire_length_stats

# Calculate the wire lengths for the current torus
wire_length_stats = calculate_wire_length_stats(phys_torus,
	cabinet_system.cabinet.rack.slot.wire_position,
	wire_length_histogram_bins)


################################################################################
# Wiring Pattern Finding
################################################################################


def get_relative_wires(boards, direction):
	"""
	Returns a list of (coord, wire_relative_target) tuples where coord is a
	coordinate of a board and wire_relative_target is the coordinate relative to
	coord of the wire going in direction from coord.
	"""
	
	b2c = dict(boards)
	
	out = []
	
	for board, coord in boards:
		out.append((coord, b2c[board.follow_wire(direction)] - coord))
	
	return out


def group_relative_wires(rel_wires, group_key, elem_key):
	"""
	Group together relative wire descriptions. Returns a dict {key:
	frozenset([(elem,wire_direction,wire_relative_target),...]), ...} where key is
	a value returned by group_key(coord) and where the elem is returned by
	elem_key(coord).
	
	For example, to group together all relative wires for each rack in the system,
	group_key = (lambda (c,r,s): (c,r))
	elem_key  = (lambda (c,r,s): s)
	"""
	
	groups = defaultdict(set)
	
	for coord, wire_relative_target in rel_wires:
		groups[group_key(coord)].add((elem_key(coord), wire_relative_target))
	
	return dict((g, frozenset(s)) for (g,s) in groups.iteritems())


def distinct_count(iterable):
	"""
	Returns a dict {item: count,...} which contains the number of times
	each unique item has appeared in the iterable
	"""
	
	counts = defaultdict(lambda:0)
	
	for item in iterable:
		counts[item] += 1
	
	return counts


def generate_cabinet_colouring_diagram(colouring, num_colours, cabinet_system, cabinet_scale):
	"""
	Takes a dict {cabinet_coord: colour_index} and the maximum color_index. Returns
	a diagram for a coloured set of racks.
	"""
	d = diagram.Diagram()
	d.set_cabinet_system(cabinet_system, cabinet_scale)
	
	
	# Generate pallet
	colours = []
	spectrum = ["red","green","blue", "yellow"]
	segment_size = (num_colours+len(spectrum)-2) / (len(spectrum)-1)
	for i in range(num_colours):
		start_colour, end_colour = spectrum[i / segment_size:][:2]
		point = 100 - (((i % segment_size) * 100) / segment_size)
		colours.append("%s!%d!%s"%(start_colour, point, end_colour))
	
	# Add the boards
	for coord, colour_index in colouring.iteritems():
		d.add_board_cabinet(coord, coord, ["fill=%s"%colours[colour_index]])
	
	return d


# A dict {filter_name : {direction: tikz, ...}, ...}
wiring_uniqueness_diagram_tikz = defaultdict(dict)

#wc = 0
for wire_filter, filter_name in [ ((lambda o: o[0]==0 and o[1]==0), "Change Slot")
                                , ((lambda o: o[0]==0 and o[1]!=0), "Change Rack")
                                , ((lambda o: o[0]!=0), "Change Cabinet")
                                ]:
	#print filter_name
	for direction in [NORTH, EAST, SOUTH_WEST]:
		#print DIRECTION_NAMES[direction]
		# Get a list of wires going in this direction with their coordinates
		# converteed to relative values. Filter out wires we're not interested in,
		# e.g. ones which leave the rack
		relative_wires = [ (c,o) for (c,o)
		                   in get_relative_wires(cabinet_torus, direction)
		                   if wire_filter(o)
		                 ]
		
		# Collect together wires which have the same relative connection
		grouped_relative_wires = group_relative_wires(relative_wires
		                                             , (lambda (c,r,s): (c,r,s))
		                                             , (lambda (c,r,s): None)
		                                             )
		
		# Count the number of times each distinct pattern of wiring occurs
		distinct_pattern_counts = distinct_count(grouped_relative_wires.itervalues())
		
		# Create a lookup from distinct pattern to a unique id
		pattern2id = dict((p,i) for (i,p) in enumerate(distinct_pattern_counts.keys()))
		
		d = generate_cabinet_colouring_diagram(
			dict( (coordinates.Cabinet(*coord), pattern2id[pattern])
			      for (coord, pattern) in grouped_relative_wires.iteritems()
			    ),
			(max(pattern2id.itervalues()) + 1 if pattern2id else 1),
			cabinet_system,
			cabinet_diagram_scaling_factor,
		)
		wiring_uniqueness_diagram_tikz[filter_name][direction] = d.get_tikz()
		
		#out = ""
		#for r in range(num_racks_per_cabinet):
		#	for c in range(num_cabinets):
		#		for s in range(num_slots_per_rack):
		#			try:
		#				out += "%X"%(distinct_relative_wire_indexes.index(grouped_relative_wires[(c,r,s)]))
		#				wc += 1
		#			except KeyError:
		#				# No local wires in this area
		#				out += "-"
		#		out += "  "
		#	out += "\n"
		#
		#print out
#print wc


################################################################################
# Board Position List Generation
################################################################################

def generate_board_position_list(boards, b2c):
	"""
	Lists the position of each board.
	"""
	out = ""
	for board, coord in sorted(boards, key = (lambda(b,c):tuple(b2c[b]))):
		out += "(%d,%d) & %d & %d & %d \\\\\n"%(
			b2c[board].x,
			b2c[board].y,
			coord.cabinet,
			coord.rack,
			coord.slot,
		)
	
	return out

board_position_list = generate_board_position_list(cabinet_torus, board2coord)


################################################################################
# Wiring Instruction Generation
################################################################################

def generate_wiring_list(wires):
	"""
	Generates a table of wiring information from a given list of wires
	"""
	
	return (r"""
	\begin{wiringtable}
	%s
	\end{wiringtable}
	"""%(
		"\n".join(r"\wire{%d}{%d}{%d}{%s}{%d}{%d}{%d}{%s}"%tuple(
				list(source) + list(target)
			)
			for source,target in sorted(wires)
		)
		
	)).strip()


def generate_wiring_instructions(boards, socket_names):
	# Instructions for wiring systems up
	
	out = ""
	
	b2c = dict(boards)
	
	wires = []
	for board, source_coord in cabinet_torus:
		for direction in [NORTH, EAST, SOUTH_WEST]:
			target_coord = b2c[board.follow_wire(direction)]
			
			source = tuple(list(source_coord) + [socket_names[direction]])
			target = tuple(list(target_coord) + [socket_names[topology.opposite(direction)]])
			
			# List wires in bottom-left to top-right order
			wires.append(tuple(sorted([source,target])))
	
	# (cabinet,rack) -> [wire,...]
	wires_between_slots = defaultdict(list)
	# (cabinet) -> [wire,...]
	wires_between_racks = defaultdict(list)
	# [wire,...]
	wires_between_cabinets = []
	
	for source, target in wires:
		if source[0:2] == target[0:2]:
			# Same cabinet and rack
			wires_between_slots[(source[0:2])].append((source,target))
		elif source[0] == target[0]:
			# Same cabinet
			wires_between_racks[source[0]].append((source,target))
		else:
			# Different cabinet
			wires_between_cabinets.append((source,target))
	
	# Within-rack wires
	out += r"\subsection{Wires Within Racks}"
	for cabinet_num in range(num_cabinets):
		for rack_num in range(num_racks_per_cabinet):
			out += r"\subsubsection{Cabinet %d, Rack %d}"%(cabinet_num, rack_num)
			out += generate_wiring_list(wires_between_slots[(cabinet_num,rack_num)])
	
	# Within-cabinet wires
	if wires_between_racks:
		out += r"\newpage\subsection{Wires Within Cabinets}"
		for cabinet_num in range(num_cabinets):
			out += r"\subsubsection{Cabinet %d}"%(cabinet_num)
			out += generate_wiring_list(wires_between_racks[(cabinet_num)])
	
	# Global wires
	if wires_between_cabinets:
		out += r"\newpage\subsection{Wires Between Cabinets}"
		out += generate_wiring_list(wires_between_cabinets)
	
	return out

wiring_instructions = generate_wiring_instructions(cabinet_torus, socket_names)


 ##############################################################################
################################################################################
# Generate Report
################################################################################
 ##############################################################################

################################################################################
# Preamble
################################################################################
print (r"""
\documentclass[a4paper,11pt]{article}

\usepackage{fullpage}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{amsmath}
\usepackage[pdftex]{lscape}
\usepackage{tikz}

\title{%(title)s}
\author{%(author)s}
\date{\today}

\begin{document}

\maketitle
\setcounter{tocdepth}{2}
\tableofcontents
"""%{
	"title":title,
	"author":"Generated By The `SpiNNer' Wiring Guide Generator",
}).strip()



################################################################################
# Introduction
################################################################################

print (r"""
\section{Introduction}

This is an automatically generated wiring guide for a SpiNNaker system. This
document covers a system with the basic parameters listed in Table
\ref{tab:basic-params}.

\begin{table}[h]
	\center
	\begin{tabular}{l r l}
		\toprule
			Parameter & Value & Unit \\
		\midrule
			Width  & %(width)d & Threeboards \\
			Height & %(height)d & Threeboards \\
		\addlinespace
			Compress Direction & %(compress_rows)s & \\
		\addlinespace
			Number of Folds & %(num_folds_x)d & X-Axis \\
			Number of Folds & %(num_folds_y)d & Y-Axis \\
		\addlinespace
			Cabinets          & %(num_cabinets)d & \\
			Racks per Cabinet & %(num_racks_per_cabinet)d & \\
			Slots per Rack    & %(num_slots_per_rack)d & \\
		\bottomrule
	\end{tabular}
	
	\caption{Basic Machine Parameters}
	\label{tab:basic-params}
\end{table}

\subsection{About This Guide}

Much of this document is based on a \emph{`Summary of Building a Toroid using
Hexagons'} by Simon Davidson and through conversations and emails with, amongst
others, Simon and Steve Furber.

"""%{
	"width":width,
	"height":height,
	"num_folds_x":num_folds_x,
	"num_folds_y":num_folds_y,
	"num_cabinets":num_cabinets,
	"num_racks_per_cabinet":num_racks_per_cabinet,
	"num_slots_per_rack":num_slots_per_rack,
	"compress_rows":"Rows" if compress_rows else "Columns",
}).strip()



################################################################################
# Wring Metrics
################################################################################

if show_wiring_metrics: print (r"""
\newpage
\section{Wiring Metrics}

\begin{table}[h]
	\center
	\begin{tabular}{l r r r r}
		\toprule
			Axis & Total Wires & Staying In-Rack & Between Racks & Between Cabinets \\
		\midrule
			%(wire_cabinet_stats)s
		\addlinespace
			%(total_wire_cabinet_stats)s
		\bottomrule
	\end{tabular}
	\caption{Wire counts within racks. Note: `Between Racks' counts wires which only
	leave the rack but stay in the same cabinet.}
	\label{tab:wire-cabinet-stats}
\end{table}

\begin{table}[h]
	\center
	\begin{tabular}{l r r r r}
		\toprule
			Axis & Length (%(cabinet_unit)s) & Number of Wires\\
		\midrule
			%(wire_length_stats)s
		\bottomrule
	\end{tabular}
	\caption{Lengths of wires in the system based on given cabinet measurements.
	Note: no slack is given to any of the wires.}
	\label{tab:wire-length-stats}
\end{table}

"""%{
	"wire_cabinet_stats":wire_cabinet_stats,
	"total_wire_cabinet_stats":total_wire_cabinet_stats,
	"wire_length_stats":wire_length_stats,
	"cabinet_unit":cabinet_unit,
}).strip()



################################################################################
# Topology Metrics
################################################################################

if show_topology_metrics: print (r"""
\newpage
\section{Topology Metrics}

Note: A wiring loop is the loop taken by following wires of a given direction in
a system (see Figure \ref{fig:wiring-loop}). A packet loop is the loop taken by
following the path of a packet within the system (see Figure
\ref{fig:packet-loop}). All displayed values found by simulation in a model.

\begin{table}[h]
	\center
	\begin{tabular}{l r l}
		\toprule
			Property & Value & Unit \\
		\midrule
			Width  & %(width)d  & Threeboards \\
			Height & %(height)d & Threeboards \\
			\addlinespace
			Width  & %(width_boards)d & Boards \\
			Height & %(height_boards)d & Boards \\
			\addlinespace
			Wiring Loop North Length      & %(wiring_loop_north_length)d      & Wires \\
			Wiring Loop East Length       & %(wiring_loop_east_length)d       & Wires \\
			Wiring Loop South West Length & %(wiring_loop_south_west_length)d & Wires \\
			\addlinespace
			Packet Loop North Length      & %(packet_loop_north_length)d      & Chips \\
			Packet Loop East Length       & %(packet_loop_east_length)d       & Chips \\
			Packet Loop South West Length & %(packet_loop_south_west_length)d & Chips \\
		\bottomrule
	\end{tabular}
	\caption{Overview of properties of the system.}
	\label{tab:topology-overview}
\end{table}


\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(wiring_loop_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Example wiring loops from (0,0). Solid lines are wires, dashed
		lines are paths through a board. Colour key: %(colour_key)s.}
		\label{fig:wiring-loop}
	\end{figure}
\end{landscape}

\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(packet_loop_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Example packet loops from (0,2), (1,1) and (0,0) for
		%(colour_key)s. Solid lines are wires, dashed lines are paths through a
		board.}
		\label{fig:packet-loop}
	\end{figure}
\end{landscape}

"""%{
	"width":width,
	"height":height,
	"width_boards":width_boards,
	"height_boards":height_boards,
	"wiring_loop_north_length":wiring_loop_north_length,
	"wiring_loop_east_length":wiring_loop_east_length,
	"wiring_loop_south_west_length":wiring_loop_south_west_length,
	"packet_loop_north_length":packet_loop_north_length,
	"packet_loop_east_length":packet_loop_east_length,
	"packet_loop_south_west_length":packet_loop_south_west_length,
	"wiring_loop_diagram_tikz":wiring_loop_diagram_tikz,
	"packet_loop_diagram_tikz":packet_loop_diagram_tikz,
	"colour_key":colour_key,
	"scale":diagram_scaling,
}).strip()


################################################################################
# Development of Placement
################################################################################

if show_development: print (r"""
\section{Development of Board Placement}

Boards must be placed in the physical world such that the maximum wire-length is
kept short. The following development describes how the boards are placed in a
physical system.

The system schematically looks like Figure \ref{fig:torus}. All touching boards
have a link between them. Links to non-adjacent boards are shown using coloured
lines.

All boards left of $(0,0)$ (shown by a dashed line) are shifted to the right
yielding a rectangle as shown in Figure \ref{fig:rect-torus}.

Before continuing, the `wobble' between consecutive columns is removed to form a
regular grid as shown in Figure \ref{fig:comp-torus}. This regular grid is then
folded into %(num_folds_x)d sheet%(num_folds_x_plural)s horizontally and
%(num_folds_y)d sheet%(num_folds_y_plural)s vertically along the lines shown in
Figure \ref{fig:fold-spaced-torus}.

After folding, the nodes from overlapping folds are interleaved to yield the
arrangement in Figure \ref{fig:folded-torus}. This diagram is shown with gaps
dividing the nodes into %(num_cabinets)d cabinet%(num_cabinets_plural)s
containing %(num_racks_per_cabinet)d rack%(num_racks_per_cabinet_plural)s each.

The rows of nodes in the blocks allocated to each rack are then interleaved to
allocate them to a slot resulting a final slot allocation for each board.  A
scale-drawing of the system as assigned to cabinets is given in Figure
\ref{fig:cabinet-torus}.

\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Schematic representation of a torus of boards. Nodes to the left of
		the dashed line will be shifted right in the next step. Wire colour key:
		%(colour_key)s}
		\label{fig:torus}
	\end{figure}
\end{landscape}

\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(rect_torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Rectangular arrangement of nodes. Colour key: %(colour_key)s}
		\label{fig:rect-torus}
	\end{figure}
\end{landscape}

\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(comp_torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Nodes forced into a regular, rectangular grid. Colour key: %(colour_key)s}
		\label{fig:comp-torus}
	\end{figure}
\end{landscape}

\begin{landscape}
	\begin{figure}
		\center
		\begin{tikzpicture}[scale=%(scale)f]
			%(fold_spaced_torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Lines along which the grid will be folded (wires removed for
		clarity).}
		\label{fig:fold-spaced-torus}
	\end{figure}
\end{landscape}

\begin{landscape}
	\enlargethispage{3cm}
	\begin{figure}
		\center
		%% Scaled additionally on the y axis so it actually fits
		\begin{tikzpicture}[scale=%(scale)f,yscale=0.8]
			%(folded_torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Arrangement after folding and interleaving shown divided into
		cabinets/racks. Colour key: %(colour_key)s}
		\label{fig:folded-torus}
	\end{figure}
\end{landscape}

\begin{landscape}
	\begin{figure}
		\center
		%% Scaled already.
		\begin{tikzpicture}
			%(cabinet_torus_diagram_tikz)s
		\end{tikzpicture}
		
		\caption{Allocation of SpiNNaker boards to cabinets and racks and the wires
		between them. Colour key: %(colour_key)s}
		\label{fig:cabinet-torus}
	\end{figure}
\end{landscape}

"""%{
	"torus_diagram_tikz":torus_diagram_tikz,
	"rect_torus_diagram_tikz":rect_torus_diagram_tikz,
	"comp_torus_diagram_tikz":comp_torus_diagram_tikz,
	"fold_spaced_torus_diagram_tikz":fold_spaced_torus_diagram_tikz,
	"folded_torus_diagram_tikz":folded_torus_diagram_tikz,
	"cabinet_torus_diagram_tikz":cabinet_torus_diagram_tikz,
	"scale":diagram_scaling,
	"colour_key":colour_key,
	"num_folds_x":num_folds_x,
	"num_folds_y":num_folds_y,
	"num_folds_x_plural":"" if num_folds_x == 1 else "s",
	"num_folds_y_plural":"" if num_folds_y == 1 else "s",
	"num_cabinets":num_cabinets,
	"num_racks_per_cabinet":num_racks_per_cabinet,
	"num_cabinets_plural":"" if num_cabinets == 1 else "s",
	"num_racks_per_cabinet_plural":"" if num_racks_per_cabinet == 1 else "s",
}).strip()


################################################################################
# Wiring Patterns
################################################################################


#\wud{%(wiring_uniqeness_slot_north)s}{wires within a rack going North}{wud-slot-north}
#\wud{%(wiring_uniqeness_slot_east)s}{wires within a rack going East}{wud-slot-east}
#\wud{%(wiring_uniqeness_slot_south_west)s}{wires within a rack going South-West}{wud-slot-south-west}

#\wud{%(wiring_uniqeness_rack_north)s}{wires between racks going North}{wud-rack-north}
#\wud{%(wiring_uniqeness_rack_east)s}{wires between racks going East}{wud-rack-east}
#\wud{%(wiring_uniqeness_rack_south_west)s}{wires between racks going South-West}{wud-rack-south-west}

#\wud{%(wiring_uniqeness_cabinet_north)s}{wires between cabinets going North}{wud-cabinet-north}
#\wud{%(wiring_uniqeness_cabinet_east)s}{wires between cabinets going East}{wud-cabinet-east}
#\wud{%(wiring_uniqeness_cabinet_south_west)s}{wires between cabinets going South-West}{wud-cabinet-south-west}


if show_wiring_patterns: print (r"""
\section{Wiring Patterns}

\newcommand{\wud}[3]{
\begin{landscape}
	\begin{figure}
		\center
		%% Scaled already.
		\begin{tikzpicture}
			#1
		\end{tikzpicture}
		
		\caption{Wiring pattern diagram for #2. Slots which have the same colour
		have a wire going to the same relative location.}
		\label{fig:#3}
	\end{figure}
\end{landscape}
}


\wud{%(wiring_uniqeness_cabinet_south_west)s}{wires between cabinets going South-West}{wud-cabinet-south-west}

"""%{
	"wiring_uniqeness_slot_north":wiring_uniqueness_diagram_tikz["Change Slot"][NORTH],
	"wiring_uniqeness_slot_east":wiring_uniqueness_diagram_tikz["Change Slot"][EAST],
	"wiring_uniqeness_slot_south_west":wiring_uniqueness_diagram_tikz["Change Slot"][SOUTH_WEST],
	
	"wiring_uniqeness_rack_north":wiring_uniqueness_diagram_tikz["Change Rack"][NORTH],
	"wiring_uniqeness_rack_east":wiring_uniqueness_diagram_tikz["Change Rack"][EAST],
	"wiring_uniqeness_rack_south_west":wiring_uniqueness_diagram_tikz["Change Rack"][SOUTH_WEST],
	
	"wiring_uniqeness_cabinet_north":wiring_uniqueness_diagram_tikz["Change Cabinet"][NORTH],
	"wiring_uniqeness_cabinet_east":wiring_uniqueness_diagram_tikz["Change Cabinet"][EAST],
	"wiring_uniqeness_cabinet_south_west":wiring_uniqueness_diagram_tikz["Change Cabinet"][SOUTH_WEST],
}).strip()


################################################################################
# Board Position List
################################################################################

if show_board_position_list: print (r"""
\section{Board Position List}

The following table lists the location of each logical (hexagonal) board address
in the cabinet system.


\vspace{1ex}

\begin{longtable}{r r r r}
		\toprule
			Coordinate & Cabinate & Rack & Slot \\
		\midrule%%
	\endhead
		\bottomrule
	\endfoot
	%(board_position_list)s
\end{longtable}

"""%{
	"board_position_list":board_position_list,
}).strip()


################################################################################
# Wiring Instructions
################################################################################

if show_wiring_instructions: print (r"""

\section{Wiring Instructions}

This series of tables lists connections which need to be made in the system.
Wiring is listed first for wires within a cabinet, then between racks, then
between cabinets.

\vspace{1ex}

\newenvironment{wiringtable}{
	\begin{longtable}{r r r l c r r r l}
		\toprule
			\multicolumn{4}{c}{From} & & \multicolumn{4}{c}{To} \\
			Cab. & Rack & Slot & Socket &$\rightarrow$& Cab. & Rack & Slot & Socket \\
		\midrule%%
	\endhead
		\bottomrule
	\endfoot
}{%%
	\end{longtable}
}
\newcommand{\wire}[8]{#1 & #2 & #3 & #4 & $\rightarrow$ & #5 & #6 & #7 & #8\\}

%%\begin{wiringtable}
%%\wire{0}{0}{0}{0}{0}{0}{0}{0}
%%\end{wiringtable}

%(wiring_instructions)s


"""%{
	"wiring_instructions":wiring_instructions,
}).strip()


################################################################################
# End Matter
################################################################################
print (r"""
\end{document}
""").strip()



