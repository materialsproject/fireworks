# {{header}}
vmdcon -info "tcl version [info patchlevel]"
source jlh_vmd.tcl
namespace import ::JlhVmd::*
use_{{surfactant}}

# scale indenter by this value to match desired lattice constant
set ::JlhVmd::scale_factor {{ scale_factor|default(1.0943,true) }}

# shift tip as to z-center apex 12 nm above substrate
set ::JlhVmd::desired_distance {{ desired_distance|default(120.0,true) }}

# distance within which molecules are regarded as overlapping
set ::JlhVmd::overlap_distance {{ overlap_distance|default(2.0,true) }}

# clip indenter that far away from cell boundary:
set ::JlhVmd::padding_distance {{ padding_distance|default(5.0,true) }}

if { [catch {
  batch_process_pdb_visual {{interface_file}} {{indenter_file}} {{output_prefix}}
} errmsg ] } {
  vmdcon -err "error:  $errmsg"
  exit 1
}
exit 0
