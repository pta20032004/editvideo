from video_overlay import add_video_overlay_with_chroma
import os

if __name__ == "__main__":
    main_video_path = r"E:\Downloads\0622.mp4"
    overlay_video_path = r"videoinput\greenscreen.mp4"
    output_path = "E:\Downloads\output_overlay_result.mp4"

    
    if not os.path.exists(main_video_path):
        print("❌ Không tìm thấy video nền")
    if not os.path.exists(overlay_video_path):
        print("❌ Không tìm thấy video overlay")
    # Thông số ĐÃ xác định phù hợp nhất cho video của bạn
    # chroma_color = "0x00ff00"
    # màu đen
    # chroma_color = "0x000000"
    #màu xanh lá
    chroma_color = "0x00ff00"
    chroma_similarity = 0.15
    chroma_blend = 0.1

    add_video_overlay_with_chroma(
        main_video_path=main_video_path,
        overlay_video_path=overlay_video_path,
        output_path=output_path,
        start_time=2,
        duration=8,
        position="center",
        size_percent=100,
        chroma_key=True,
        chroma_color=chroma_color,
        chroma_similarity=chroma_similarity,
        chroma_blend=chroma_blend
    )

    print(f"✅ Đã tạo video kết quả: {output_path}")
