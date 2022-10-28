# Maxwell and Linnea Test Plugin
from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa

# new module for ParaView-specific decorators.
from paraview.util.vtkAlgorithm import smproxy, smproperty, smdomain

from paraview import vtk
import numpy as np # needed for interpolation and pi

import math
import copy

@smproxy.filter(label="Test Filter")
@smproperty.input(name="Input")
class VTStoVTSonSphere(VTKPythonAlgorithmBase):


    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=1, nOutputPorts=1)

        # Set the default amountToAdd value to 0
        self.amountToAdd = 0

        # Set the default columnAtEnd value to 0
        self.columnAtEnd = 0

        # Set the default arrayToAlter value to an empty string
        self.arrayToAlter = ""

        # Create a list of the array names inside of the input data set
        self._availableArrays = ["Sea Level Change (m)", "test"]

    def FillInputPortInformation(self, port, info):
        info.Set(vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet")
        return 1

    def FillOutputPortInformation(self, port, info):
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkStructuredGrid")
        return 1

    @smproperty.xml("""
        <IntVectorProperty name="AddColumnToOneEnd"
            number_of_elements="1"
            default_values="0"
            command="SetColumnAtEnd">
            <BooleanDomain name="bool" />
            <Documentation>This creates a dummy checkbox widget. The text here will be
            displayed when you hover over the checkbox.
            </Documentation>
        </IntVectorProperty>""")
    def SetColumnAtEnd(self, x):
        self.columnAtEnd = x
        print("Set Column At End: ", self.columnAtEnd)
        self.Modified()

    def GetColumnAtEnd(self):
        print("Get Column At End: ", self.columnAtEnd)
        return self.columnAtEnd

    # Create a slider in the UI for the user to specify the warp scale factor with its
    # range fetched at runtime. For int values,
    # use `intvector` and `IntRangeDomain` instead of the double variants used
    # below.
    @smproperty.doublevector(name="AmountToAddValue", information_only="1")
    def GetValueRange(self):
        print("getting range: (0, 20000)")
        return (0, 20000)

    @smproperty.doublevector(name="AmountToAdd", default_values=[0.0])
    @smdomain.xml(\
        """<DoubleRangeDomain name="range" default_mode="mid">
                <RequiredProperties>
                    <Property name="AmountToAddValue" function="RangeInfo" />
                </RequiredProperties>
           </DoubleRangeDomain>
        """)
    def SetValue(self, val):
        print("settings value:", val)
        self.amountToAdd = val
        self.Modified()
    
    @smproperty.stringvector(name="AvailableScalarArrays", information_only="1")
    def GetAvailableArrays(self):
        return (self._availableArrays)
        #return (self.arrayToWarpBy)

    @smproperty.stringvector(name="ScalarArrayToAlter", number_of_elements="1")
    @smdomain.xml(\
        """ <StringListDomain name="axisChoice">
                <RequiredProperties>
                    <Property name="AvailableScalarArrays"
                        function="AxisSelection"/>
                </RequiredProperties>
        </StringListDomain>
        """)
    def SetAxis(self, val):
        print("Setting ", val)
        self.arrayToAlter = val
        self.Modified()

    def RequestData(self, request, inInfo, outInfo):

        print("I am running RequestData")

        AMOUNT_TO_ADD_TO_ARRAY = self.amountToAdd

        # get the first input.
        inputDataSet0 = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))

        # Check that the Add Column To One End checkbox is checked, and if it
        # is, then print that the checkbox is checked.
        if (self.GetColumnAtEnd() == True):
            print("The checkbox widget is checked.")

        newPoints = vtk.vtkPoints()
        numPoints = inputDataSet0.GetNumberOfPoints()
        
        num_arrays = inputDataSet0.GetPointData().GetNumberOfArrays()
        print("Number of arrays:", num_arrays)

        # Get the dimensions of the input dataset
        input_dimensions = inputDataSet0.GetDimensions()


        print("Dimensions:")
        print(input_dimensions[0])   # should be 1025
        print(input_dimensions[1])   # should be 512
        print(input_dimensions[2])   # should be 1

        x_dimension = input_dimensions[0]
        y_dimension = input_dimensions[1]
        z_dimension = input_dimensions[2]

        oldPointVals = inputDataSet0.GetPointData().GetArray(self.arrayToAlter)

        # Insert the points in newPoints. You can change the position of the points in your output
        # data set here.
        for i in range(0, numPoints):
            coord = inputDataSet0.GetPoint(i)
            rX, rY, rZ = coord[:3]
            newPoints.InsertPoint(i,rX,rY,rZ)

        # Create the output data set
        outputDataSet = vtk.vtkStructuredGrid.GetData(outInfo)


        # Loop through each of the scalar arrays in the dataset
        # and add the array to the output dataset
        for j in range(0, num_arrays):
            ivals = inputDataSet0.GetPointData().GetArray(j)
            #ivals = newDataSet.GetPointData().GetArray(j)
            ca = vtk.vtkFloatArray()
            ca.SetName(ivals.GetName())
            ca.SetNumberOfComponents(1)
            ca.SetNumberOfTuples(numPoints)

            #add the new array to the output
            outputDataSet.GetPointData().AddArray(ca)


            #copy the values over element by element
            for i in range(0, numPoints):

                # I tried to check whether the ivals array was the same as the array the
                # user selected, but the comparison I was using caused ParaView to stop
                # responding. You can try getting this comparison to work to be able to 
                # add a constant to the array values.

                #comparisonOfArrays = oldPointVals == ivals
                #if (comparisonOfArrays.all()): # The array is the same as the one the user selected
                    #newVal = ivals.GetValue(i) + AMOUNT_TO_ADD_TO_ARRAY
                    #ca.SetValue(i, newVal)
                #else:
                    #ca.SetValue(i, ivals.GetValue(i))
                ca.SetValue(i, ivals.GetValue(i))

        outputDataSet.SetDimensions(x_dimension,y_dimension,z_dimension)
        outputDataSet.SetPoints(newPoints)

        return 1

    def RequestInformation(self, request, inInfo, outInfo):
        print("I am running RequestInformation")
        #print("I am running RequestInformation")

        # get the first input.
        inputDataSet0 = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))

        # Get the list of array names from the input data set and assign that list to the
        # availableArrays variable
        num_arrays = inputDataSet0.GetPointData().GetNumberOfArrays()

        # Create a list of the array names inside of the input data set
        array_list = []
        for i in range(num_arrays):
            array_name = inputDataSet0.GetPointData().GetArray(i).GetName()
            array_list.append(array_name)
        self._availableArrays = array_list
        
        # Get the dimensions of the input dataset
        inputData = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))
        input_dimensions = inputData.GetDimensions()
        x_dimension = input_dimensions[0]
        y_dimension = input_dimensions[1]
        z_dimension = input_dimensions[2]


        executive = self.GetExecutive()
        outInfo = executive.GetOutputInformation(0)
        outInfo.Set(executive.WHOLE_EXTENT(), 0, x_dimension, 0, (y_dimension - 1), 0, 0)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        print("I am running RequestUpdateExtent")

        
        # Get the dimensions of the input dataset
        inputData = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))
        input_dimensions = inputData.GetDimensions()
        x_dimension = input_dimensions[0]
        y_dimension = input_dimensions[1]
        z_dimension = input_dimensions[2]


        executive = self.GetExecutive()
        inInfo = executive.GetInputInformation(0, 0)
        inInfo.Set(executive.UPDATE_EXTENT(), 0, (x_dimension - 1), 0, (y_dimension - 1), 0, 0)
        return 1
