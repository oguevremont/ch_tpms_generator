# 1. Generate the Excel file with all cases
# 2. Generate the media
# 3. Loop over all the generated media for analysis

import create_xlsx_from_parameters_sets
import generation_from_xlsx
import postprocess_generated_media
import stl_to_rbf
import cfd_using_lethe
import postprocess_cfd_results

# 1. 
create_xlsx_from_parameters_sets.run()
# 2. 
generation_from_xlsx.run()
# 3. 
postprocess_generated_media.run()
# 4. 
#stl_to_rbf.run()
# 5. 
#cfd_using_lethe.run()
# 6.
#postprocess_cfd_results.run()