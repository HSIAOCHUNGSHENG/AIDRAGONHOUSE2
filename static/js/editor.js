// 初始化富文本編輯器
document.addEventListener('DOMContentLoaded', function() {
    // 如果頁面中有Rich Text Editor需要初始化
    if (document.getElementById('content') || document.getElementById('description')) {
        // 使用本地託管的TinyMCE
        if (!window.tinymce) {
            var script = document.createElement('script');
            script.src = '/static/tinymce/tinymce/js/tinymce/tinymce.min.js';
            script.referrerpolicy = 'origin';
            document.head.appendChild(script);
            
            script.onload = function() {
                initTinyMCE();
            };
        } else {
            initTinyMCE();
        }
    }
    
    // 初始化TinyMCE編輯器
    function initTinyMCE() {
        const editorConfig = {
            height: 400,
            menubar: false,
            plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount',
            toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table | align lineheight | numlist bullist indent outdent | emoticons charmap | removeformat',
            content_style: "body { font-family:Helvetica,Arial,sans-serif; font-size:16px; max-width:100%; overflow-wrap:break-word; }",
            width: "100%",
            force_root_block: "p",
            force_br_newlines: false,
            forced_root_block: "p",
            
            // 設置圖片上傳功能
            images_upload_url: '/admin/upload',
            automatic_uploads: true,
            file_picker_types: 'image',
            
            // 在成功上傳圖片後的處理
            images_upload_handler: function (blobInfo, success, failure) {
                var xhr, formData;
                xhr = new XMLHttpRequest();
                xhr.withCredentials = false;
                xhr.open('POST', '/admin/upload');
            
                xhr.onload = function() {
                    var json;
                    
                    if (xhr.status != 200) {
                        failure('HTTP Error: ' + xhr.status);
                        return;
                    }
                    
                    try {
                        json = JSON.parse(xhr.responseText);
                    } catch (e) {
                        failure('Invalid JSON: ' + xhr.responseText);
                        return;
                    }
                    
                    if (!json || typeof json.location != 'string') {
                        failure('Invalid JSON structure: ' + xhr.responseText);
                        return;
                    }
                    
                    success(json.location);
                };
            
                xhr.onerror = function () {
                    failure('Image upload failed due to a XHR Transport error. Code: ' + xhr.status);
                };
            
                formData = new FormData();
                formData.append('file', blobInfo.blob(), blobInfo.filename());
            
                xhr.send(formData);
            },
            
            // 移除語言設定，使用默認英文
            setup: function(editor) {
                editor.on('change', function() {
                    editor.save(); // 保存編輯器內容到原始textarea
                });
            }
        };
        
        // 初始化新聞內容編輯器
        if (document.getElementById('content')) {
            tinymce.init({
                ...editorConfig,
                selector: '#content'
            });
        }
        
        // 初始化服務描述編輯器
        if (document.getElementById('description')) {
            tinymce.init({
                ...editorConfig,
                selector: '#description',
                height: 300
            });
        }
    }
});
