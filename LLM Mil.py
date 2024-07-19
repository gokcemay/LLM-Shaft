import adsk.core, adsk.fusion, traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct

        # 1. Get Input from User
        loadInput, isLoadCancelled = ui.inputBox('Enter the load (Newtons):', 'Shaft Design')
        if isLoadCancelled:
            return  # Exit if user cancels
        distanceInput, isDistanceCancelled = ui.inputBox('Enter the distance between supports (mm):', 'Shaft Design')
        if isDistanceCancelled:
            return  # Exit if user cancels
        load = float(loadInput)
        distance = float(distanceInput)

        # Material and safety factor (default values, can be changed in UI)
        material = 'S235'
        safetyFactor = 2
        yieldStrength = 235  # Yield strength for S235 steel (N/mm^2)

        # 2. Calculations
        maxBendingMoment = load * distance / 4
        allowableStress = yieldStrength / safetyFactor
        shaftDiameter = ((32 * maxBendingMoment) / (math.pi * allowableStress)) ** (1/3)

        # 3. Shaft Design (Using Fusion 360 API)
        rootComp = design.rootComponent

        # Create a new occurrence
        newOcc = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        newComp = adsk.fusion.Component.cast(newOcc.component)

        # Main body of the shaft (Store sketch and dimensions objects)
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        circles = sketch.sketchCurves.sketchCircles
        centerPoint = adsk.core.Point3D.create(0, 0, 0)
        circle = circles.addByCenterRadius(centerPoint, shaftDiameter / 2)
        prof = sketch.profiles.item(0)
        extrudes = newComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distanceInput = adsk.core.ValueInput.createByReal(distance / 10.0)
        extInput.setDistanceExtent(False, distanceInput)
        extrudeFeature = extrudes.add(extInput)

        # Store sketch and dimensions objects
        mainBodySketch = sketch
        mainBodyDimensions = sketch.sketchDimensions

        # 4. Dimensioning (With Error Handling)
        try:
            shaftDiameterDimension = mainBodyDimensions.addDiameterDimension(circle, adsk.core.Point3D.create(shaftDiameter / 2 + 10, 0, distance / 2))

            # Get SketchPoints collection
            sketchPoints = mainBodySketch.sketchPoints

            # Create Point3D objects from BRepVertex objects
            startVertex = newComp.bRepBodies.item(0).edges[0].startVertex
            endVertex = newComp.bRepBodies.item(0).edges[0].endVertex
            startPoint = sketchPoints.add(startVertex.geometry)
            endPoint = sketchPoints.add(endPoint.geometry)

            shaftLengthDimension = mainBodyDimensions.addDistanceDimension(
                startPoint,
                endPoint,
                adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                adsk.core.Point3D.create(0, 0, distance / 2)
            )

        except RuntimeError as e:
            if ui:
                ui.messageBox(f'Dimensioning error: {e}')

        # Display Results
        ui.messageBox(
            f"Shaft Diameter: {shaftDiameter:.2f} mm\n"
            f"Shaft Length: {distance:.2f} mm\n"
        )

    except:
        if ui:
            ui.messageBox('Error Occurred:\n{}'.format(traceback.format_exc()))
