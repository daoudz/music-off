/**
 * Music-Off: Internationalization (i18n)
 * Supports: English (en), Arabic (ar), French (fr)
 */

const translations = {
    en: {
        // Header
        appTitle: 'Music-Off',
        tagline: 'AI-Powered Music Remover',

        // Theme
        themeDark: '🌙',
        themeLight: '☀️',

        // Output section
        outputTitle: 'Output Directory',
        outputDesc: 'Where your processed files will be saved',
        outputPlaceholder: 'Enter output directory path...',
        browseBtn: '📁 Browse',
        setPathBtn: 'Set Path',

        // FFmpeg section
        ffmpegTitle: 'FFmpeg Settings',
        ffmpegDesc: 'Required for video file processing',
        ffmpegAutoDetect: 'Auto-detect FFmpeg',
        ffmpegManualPlaceholder: 'Browse to FFmpeg bin folder...',
        ffmpegBrowseBtn: '📁 Browse',
        ffmpegSetBtn: 'Set Path',
        ffmpegDetected: '✅ FFmpeg detected',
        ffmpegNotFound: '⚠ FFmpeg not found',

        // Upload
        uploadTitle: 'Drop your file here',
        uploadSubtitle: 'or click to browse',
        uploadLimit: 'Maximum 30 minutes · Up to 1GB',

        // Processing
        processingDefault: 'Preparing to process your file...',
        uploadingMsg: 'Uploading file...',
        uploadedMsg: 'File uploaded, starting AI processing...',

        // Result
        resultTitle: 'Music Removed Successfully!',
        downloadBtn: 'Download',
        newFileBtn: 'Process Another File',

        // Error
        errorTitle: 'Something went wrong',
        retryBtn: 'Try Again',

        // Footer
        footerText: 'Powered by <strong>Demucs AI</strong> by Meta · Built with ❤️',

        // Status messages
        unsupportedFormat: 'Unsupported format "{ext}". Supported: {formats}',
        fileTooLarge: 'File is too large. Maximum size is 1GB.',
        uploadFailed: 'Upload failed: {error}. Is the server running?',
        pickFolderFail: 'Failed to open folder picker',
        enterDirPath: 'Please enter a directory path',
        connectFail: 'Failed to connect to server',
        outputSetTo: '✅ Output set to: {path}',
        ffmpegSetTo: '✅ FFmpeg path set to: {path}',
    },

    ar: {
        // Header
        appTitle: 'ميوزك أوف',
        tagline: 'مزيل الموسيقى بالذكاء الاصطناعي',

        // Theme
        themeDark: '🌙',
        themeLight: '☀️',

        // Output section
        outputTitle: 'مجلد الحفظ',
        outputDesc: 'أين سيتم حفظ ملفاتك المعالجة',
        outputPlaceholder: 'أدخل مسار المجلد...',
        browseBtn: '📁 تصفح',
        setPathBtn: 'تعيين المسار',

        // FFmpeg section
        ffmpegTitle: 'إعدادات FFmpeg',
        ffmpegDesc: 'مطلوب لمعالجة ملفات الفيديو',
        ffmpegAutoDetect: 'كشف تلقائي لـ FFmpeg',
        ffmpegManualPlaceholder: 'تصفح إلى مجلد FFmpeg bin...',
        ffmpegBrowseBtn: '📁 تصفح',
        ffmpegSetBtn: 'تعيين المسار',
        ffmpegDetected: '✅ تم العثور على FFmpeg',
        ffmpegNotFound: '⚠ لم يتم العثور على FFmpeg',

        // Upload
        uploadTitle: 'أفلت ملفك هنا',
        uploadSubtitle: 'أو انقر للتصفح',
        uploadLimit: 'الحد الأقصى 30 دقيقة · حتى 1 جيجابايت',

        // Processing
        processingDefault: 'جارٍ تحضير ملفك للمعالجة...',
        uploadingMsg: 'جارٍ رفع الملف...',
        uploadedMsg: 'تم الرفع، بدء المعالجة بالذكاء الاصطناعي...',

        // Result
        resultTitle: 'تمت إزالة الموسيقى بنجاح!',
        downloadBtn: 'تحميل',
        newFileBtn: 'معالجة ملف آخر',

        // Error
        errorTitle: 'حدث خطأ',
        retryBtn: 'إعادة المحاولة',

        // Footer
        footerText: 'مدعوم بـ <strong>Demucs AI</strong> من Meta · صُنع بـ ❤️',

        // Status messages
        unsupportedFormat: 'صيغة غير مدعومة "{ext}". المدعومة: {formats}',
        fileTooLarge: 'الملف كبير جداً. الحد الأقصى 1 جيجابايت.',
        uploadFailed: 'فشل الرفع: {error}. هل الخادم يعمل؟',
        pickFolderFail: 'فشل فتح متصفح المجلدات',
        enterDirPath: 'يرجى إدخال مسار المجلد',
        connectFail: 'فشل الاتصال بالخادم',
        outputSetTo: '✅ تم تعيين مجلد الحفظ: {path}',
        ffmpegSetTo: '✅ تم تعيين مسار FFmpeg: {path}',
    },

    fr: {
        // Header
        appTitle: 'Music-Off',
        tagline: 'Suppresseur de Musique par IA',

        // Theme
        themeDark: '🌙',
        themeLight: '☀️',

        // Output section
        outputTitle: 'Répertoire de sortie',
        outputDesc: 'Où vos fichiers traités seront sauvegardés',
        outputPlaceholder: 'Entrez le chemin du répertoire...',
        browseBtn: '📁 Parcourir',
        setPathBtn: 'Définir',

        // FFmpeg section
        ffmpegTitle: 'Paramètres FFmpeg',
        ffmpegDesc: 'Requis pour le traitement des fichiers vidéo',
        ffmpegAutoDetect: 'Détection automatique de FFmpeg',
        ffmpegManualPlaceholder: 'Parcourir vers le dossier bin de FFmpeg...',
        ffmpegBrowseBtn: '📁 Parcourir',
        ffmpegSetBtn: 'Définir',
        ffmpegDetected: '✅ FFmpeg détecté',
        ffmpegNotFound: '⚠ FFmpeg introuvable',

        // Upload
        uploadTitle: 'Déposez votre fichier ici',
        uploadSubtitle: 'ou cliquez pour parcourir',
        uploadLimit: 'Maximum 30 minutes · Jusqu\'à 1 Go',

        // Processing
        processingDefault: 'Préparation du traitement de votre fichier...',
        uploadingMsg: 'Téléversement du fichier...',
        uploadedMsg: 'Fichier téléversé, démarrage du traitement IA...',

        // Result
        resultTitle: 'Musique supprimée avec succès !',
        downloadBtn: 'Télécharger',
        newFileBtn: 'Traiter un autre fichier',

        // Error
        errorTitle: 'Une erreur est survenue',
        retryBtn: 'Réessayer',

        // Footer
        footerText: 'Propulsé par <strong>Demucs AI</strong> de Meta · Créé avec ❤️',

        // Status messages
        unsupportedFormat: 'Format non pris en charge « {ext} ». Formats supportés : {formats}',
        fileTooLarge: 'Le fichier est trop volumineux. Taille maximale : 1 Go.',
        uploadFailed: 'Échec du téléversement : {error}. Le serveur est-il en marche ?',
        pickFolderFail: 'Impossible d\'ouvrir le sélecteur de dossier',
        enterDirPath: 'Veuillez entrer un chemin de répertoire',
        connectFail: 'Échec de connexion au serveur',
        outputSetTo: '✅ Sortie définie sur : {path}',
        ffmpegSetTo: '✅ Chemin FFmpeg défini sur : {path}',
    },
};

let currentLang = 'en';

/**
 * Get a translated string by key, with optional template replacements.
 * Usage: t('unsupportedFormat', { ext: '.xyz', formats: '...' })
 */
function t(key, params = {}) {
    let str = (translations[currentLang] && translations[currentLang][key])
        || translations.en[key]
        || key;
    for (const [k, v] of Object.entries(params)) {
        str = str.replace(`{${k}}`, v);
    }
    return str;
}

/**
 * Apply translations to all elements with data-i18n attribute.
 */
function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t(key);
        if (el.hasAttribute('data-i18n-html')) {
            el.innerHTML = val;
        } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = val;
        } else {
            el.textContent = val;
        }
    });
}

/**
 * Set the active language and update the entire UI.
 */
function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('musicoff-lang', lang);

    // Set RTL for Arabic
    if (lang === 'ar') {
        document.documentElement.setAttribute('dir', 'rtl');
    } else {
        document.documentElement.setAttribute('dir', 'ltr');
    }

    applyTranslations();

    // Update the language selector if it exists
    const selector = document.getElementById('langSelect');
    if (selector) selector.value = lang;
}

/**
 * Load saved language from localStorage.
 */
function loadSavedLanguage() {
    const saved = localStorage.getItem('musicoff-lang');
    setLanguage(saved || 'en');
}
