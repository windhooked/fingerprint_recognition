import numpy as np
import math
import scipy.ndimage


def frequest(im, orientim, kernel_size, minWaveLength, maxWaveLength):
    """
    Based on https://pdfs.semanticscholar.org/ca0d/a7c552877e30e1c5d87dfcfb8b5972b0acd9.pdf pg.14
    Function to estimate the fingerprint ridge frequency within a small block
    of a fingerprint image.  This function is used by RIDGEFREQ
    :param im: Image block to be processed.
    :param orientim: Ridge orientation image of image block.
    :param kernel_size: Window length used to identify peaks. This should be an odd integer, say 3 or 5.
    :param minWaveLength: Minimum and maximum ridge wavelengths, in pixels, considered acceptable.
    :param maxWaveLength: Maximum ridge wavelengths, in pixels, considered acceptable.
    :return:
        freqim: An image block the same size as im with all values set to the estimated ridge spatial frequency.  If a
                ridge frequency cannot be found, or cannot be found within the limits set by min and max Wavlength
                freqim is set to zeros.
    """
    rows,cols = np.shape(im)
    
    # Find mean orientation within the block. This is done by averaging the
    # sines and cosines of the doubled angles before reconstructing the
    # angle again.  This avoids wraparound problems at the origin.
    cosorient = np.mean(np.cos(2*orientim))
    sinorient = np.mean(np.sin(2*orientim))
    block_orient = math.atan2(sinorient,cosorient)/2
    
    # Rotate the image block so that the ridges are vertical
    #ROT_mat = cv2.getRotationMatrix2D((cols/2,rows/2),orient/np.pi*180 + 90,1)    
    #rotim = cv2.warpAffine(im,ROT_mat,(cols,rows))
    rotim = scipy.ndimage.rotate(im,block_orient/np.pi*180 + 90,axes=(1,0),reshape = False,order = 3,mode = 'nearest')

    # Now crop the image so that the rotated image does not contain any
    # invalid regions.  This prevents the projection down the columns
    # from being mucked up.
    cropsze = int(np.fix(rows/np.sqrt(2)))
    offset = int(np.fix((rows-cropsze)/2))
    rotim = rotim[offset:offset+cropsze][:,offset:offset+cropsze]

    # Sum down the columns to get a projection of the grey values down the ridges.
    ridge_sum = np.sum(rotim,axis = 0)
    dilation = scipy.ndimage.grey_dilation(ridge_sum, kernel_size, structure=np.ones(kernel_size))

    ridge_noise = np.abs(dilation - ridge_sum); peak_thresh = 2;
    maxpts = (ridge_noise<peak_thresh) & (ridge_sum > np.mean(ridge_sum))
    maxind = np.where(maxpts)
    _, NoOfPeaks = np.shape(maxind)
    
    # Determine the spatial frequency of the ridges by divinding the
    # distance between the 1st and last peaks by the (No of peaks-1). If no
    # peaks are detected, or the wavelength is outside the allowed bounds,
    # the frequency image is set to 0
    if(NoOfPeaks<2):
        freqim = np.zeros(im.shape)
    else:
        waveLength = (maxind[0][-1] - maxind[0][0])/(NoOfPeaks - 1)
        if waveLength>=minWaveLength and waveLength<=maxWaveLength:
            freqim = 1/np.double(waveLength) * np.ones(im.shape)
        else:
            freqim = np.zeros(im.shape)
    return(freqim)


def ridge_freq(im, mask, orient, block_size, kernel_size, minWaveLength, maxWaveLength):
    # Function to estimate the fingerprint ridge frequency across a
    # fingerprint image. This is done by considering blocks of the image and
    # determining a ridgecount within each block by a call to FREQEST.
    rows,cols = im.shape
    freq = np.zeros((rows,cols))

    for row in range(0, rows - block_size, block_size):
        for col in range(0, cols - block_size, block_size):
            blkim = im[row:row + block_size][:, col:col + block_size]
            blkor = orient[row // block_size][col // block_size]
            freq[row:row + block_size][:, col:col + block_size] = frequest(blkim, blkor, kernel_size, minWaveLength, maxWaveLength)

    freq = freq*mask
    freq_1d = np.reshape(freq,(1,rows*cols))
    ind = np.where(freq_1d>0)
    ind = np.array(ind)
    ind = ind[1,:]

    non_zero_elems_in_freq = freq_1d[0][ind]
    medianfreq = np.median(non_zero_elems_in_freq) *mask

    return medianfreq
