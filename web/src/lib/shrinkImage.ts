/**
 * Shrink a phone photo in the browser before uploading it.
 *
 * Why (P1, comms #0025): phones send 4–5 MB camera JPEGs, which took 20 s to 3 min to upload over mobile data
 * through the tunnel, while the engine itself needs ~3 s. The engine works on a 1000×630 card and reads e-Aadhaar
 * letters at 2200 px, so 2200 px on the long side loses nothing it uses. The phone's EXIF rotation is baked in.
 * Any failure falls back to the original file, so uploads never break because of this step.
 */
const MAX_SIDE = 2200
const QUALITY = 0.85
const SKIP_BELOW_BYTES = 900_000

export async function shrinkImage(file: File): Promise<File> {
  if (!/^image\/(jpeg|png)$/.test(file.type) || file.size < SKIP_BELOW_BYTES) return file
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
    const width = Math.round(bitmap.width * scale)
    const height = Math.round(bitmap.height * scale)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      bitmap.close()
      return file
    }
    ctx.drawImage(bitmap, 0, 0, width, height)
    bitmap.close()
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITY))
    if (!blob || blob.size >= file.size) return file
    return new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg', lastModified: Date.now() })
  } catch {
    return file
  }
}
