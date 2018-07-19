#include <stdio.h>
#include <stdint.h>
#include <math.h>


__device__ int getGlobalIdx_2D_2D(){
	int blockId = blockIdx.x + blockIdx.y * gridDim.x;
	int threadId = blockId * (blockDim.x * blockDim.y) + (threadIdx.y * blockDim.x) + threadIdx.x;
	return threadId;
}


/// Cuda Kernel Code
__global__ void slidingMaxiumum2D(float* inputArray, float* outputArray, int kernelLen, int strideRow, int strideColumn, int arrayColCount, int arrayRowCount, int* kernelFootprint){
    int threadId = getGlobalIdx_2D_2D();
    int arrayLength = arrayRowCount* arrayColCount;  // Calculate the total length of the 2d array in 1d memory space
    if(threadId >= arrayLength){                     // Take care of extra threads
    	return;
    }
    
    int memLoc = threadId*strideColumn;              // Get the offset in memory for our array
    int xLocation = memLoc % arrayColCount;          // Get the x location for each row, e.g. the end of first row will be the arrayColCount-1, and first will be 0
    int targetXLocation;
    
    int footprintLocation = ceilf(kernelLen * (kernelLen/2)) + ceilf(kernelLen/2); // Get the middle cell of our kernel since it needs to match up with our footprint (same size as kernel) and we base the kernel movement on being in the middle cell
    int targetFootprintLocation;                                                   // The footprints selected location in related to the previous variable which is the middle of our 2D kernel
    int* targetFootprintLocationPointer;                                           // The pointer to the previous variable

    int targetMemLoc;              // Our target memory location which will be used to evaluate cells around the original memLoc
    float* targetMemLocPointer;    // The pointer of the above variable
    float* outputMemLocPointer = (outputArray + memLoc); // The pointer in reference to correct coordinates in the outputArrays memory

    float maxValue = 0.0f;         // The eventual maximum after checking values in the kernel space


    for(int rowStep = -floorf(kernelLen/2); rowStep <= floorf(kernelLen/2); rowStep++){
        for(int colStep = -floorf(kernelLen/2); colStep <= floorf(kernelLen/2); colStep++){
            targetMemLoc = memLoc + (rowStep*strideRow) + (colStep*strideColumn); // Get the element in the kernel we are currently checking in the for loop
            targetMemLocPointer = (inputArray + targetMemLoc);                    // Same as above but actual memory address (pointer)
            targetXLocation = xLocation + colStep;                                // Get which column we are trying to access for edge cases

            targetFootprintLocation =  footprintLocation + (rowStep*kernelLen) + colStep; // Get the location for which cell in the footprint we want (should match up identically in shape and position to the kernel)
            targetFootprintLocationPointer = kernelFootprint + targetFootprintLocation;   // Get the pointer to get the actual value
            //printf("Footprint value is %i at: %i | %i\n", *targetFootprintLocationPointer, colStep, rowStep);
            
            // Bound Cases and evaluation
            if((targetMemLocPointer < inputArray) || (targetMemLocPointer >= inputArray + arrayLength)){ // Handle edge cases
                continue;
            }else{ // Bound cases were successful
            	if(targetXLocation >= 0 && targetXLocation < arrayColCount){      // Deal with left and right edge cases e.g. dont go below the 0 point which would go onto the different row or past the length of a row for the same reason
	                if((*targetMemLocPointer * *targetFootprintLocationPointer)> maxValue){ // If our target memory location is larger than our current largest float - but also multiplied by the footprints value of either 1 or 0 to negate this part of the kernel
	                    maxValue = *targetMemLocPointer; // Set the value
	                }
            	}
            }
        }
    }

    *outputMemLocPointer = maxValue; // At the end set the highest value to the right memory location in the outputArray
}