import os
from CSXCAD import ContinuousStructure

CSX = ContinuousStructure()

material = CSX.AddMaterial('copper')

stl_filename = '../stl/Traces_reduced.stl'
stl_reader = material.AddPolyhedronReader(stl_filename)

    
xml_filename = 'geometry.xml'
CSX.Write2XML(xml_filename)
os.system('AppCSXCAD geometry.xml')


