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
            content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:16px }',
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
