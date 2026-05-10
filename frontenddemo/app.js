class InkPrinterUI {
    constructor() {
        this.state = {
            jobId: null,
            uploadPath: null,
            printer: "A1",
            mode: "single",
            rotate: false,
            splitCompound: false,
            dimensions: null,
            colours: null,
            dockPositions: {}
        };
        this.currentStep = "upload";
        this.init();
    }

    init() {
        const app = document.getElementById("app");
        app.innerHTML = this.renderUploadForm();
        this.attachUploadListeners();
    }

    renderUploadForm() {
        return `
            <div class="form-section">
                <h2>Step 1: Upload PDF</h2>
                <div class="form-group">
                    <label for="pdf-upload">Select PDF File:</label>
                    <input type="file" id="pdf-upload" accept=".pdf" />
                </div>
                <div class="button-group">
                    <button class="primary" id="upload-btn">Upload & Analyze</button>
                </div>
            </div>
        `;
    }

    renderConfigForm() {
        return `
            <div class="form-section">
                <h2>Step 2: Configuration</h2>
                
                <div class="form-group">
                    <label for="printer">Printer:</label>
                    <select id="printer" onchange="ui.handlePrinterChange()">
                        <option value="A1 Mini">A1 Mini (180x180x180mm)</option>
                        <option value="A1">A1 (255x255x240mm)</option>
                        <option value="P1S/P2S">P1S/P2S (240x255x255mm)</option>
                        <option value="H2D">H2D (325x325x320mm)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Print Mode:</label>
                    <div class="radio-group">
                        <div>
                            <input type="radio" id="mode-single" name="mode" value="single" checked onchange="ui.handleModeChange()">
                            <label for="mode-single">Single Colour</label>
                        </div>
                        <div>
                            <input type="radio" id="mode-multi" name="mode" value="multi" onchange="ui.handleModeChange()">
                            <label for="mode-multi">Multi Colour</label>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <div class="alert alert-info">
                        <strong>Layout:</strong> ${this.state.dimensions?.layout || 'Detecting...'}
                        <br><strong>Dimensions:</strong> ${this.state.dimensions?.width.toFixed(1) || '-'} × ${this.state.dimensions?.height.toFixed(1) || '-'} mm
                    </div>
                </div>

                <div class="checkbox-group">
                    <input type="checkbox" id="rotate" ${this.state.dimensions?.needs_rotation ? 'checked' : 'disabled'} onchange="ui.handleRotationChange()">
                    <label for="rotate">Rotate to Landscape</label>
                </div>

                <div class="checkbox-group">
                    <input type="checkbox" id="split-compound" onchange="ui.handleSplitChange()">
                    <label for="split-compound">Split Compound Paths</label>
                </div>

                <div class="button-group">
                    <button class="secondary" onclick="ui.goBack()">Back</button>
                    <button class="primary" id="next-btn" onclick="ui.checkDimensions()">Check Dimensions</button>
                </div>
            </div>
        `;
    }

    renderDimensionCheckForm() {
        const dims = this.state.dimensions;
        const fits = dims.fits;
        
        return `
            <div class="form-section">
                <h2>Step 3: Dimension Check</h2>
                
                ${fits ? 
                    `<div class="alert alert-success">
                        ✓ PDF dimensions fit within printer bounds!
                    </div>` 
                    : 
                    `<div class="alert alert-warning">
                        ⚠ PDF dimensions exceed printer bounds. Scaling required.
                    </div>`
                }

                <div class="dimensions-display">
                    <p><strong>PDF Dimensions:</strong> ${dims.width.toFixed(1)} × ${dims.height.toFixed(1)} mm</p>
                    <p><strong>Printer Bounds:</strong> ${dims.max_x} × ${dims.max_y} mm</p>
                    ${!fits ? `<p><strong class="dimension-warning">Required Scale:</strong> ${(dims.required_scale * 100).toFixed(1)}%</p>` : ''}
                </div>

                <div class="button-group">
                    <button class="secondary" onclick="ui.goBack()">Back</button>
                    ${fits ? 
                        `<button class="primary" onclick="ui.proceedToColours()">Continue</button>` 
                        : 
                        `<button class="secondary" onclick="ui.goBack()">Try Different Printer</button>
                         <button class="primary" onclick="ui.proceedToColours()">Proceed with Scaling</button>`
                    }
                </div>
            </div>
        `;
    }

    renderColourSelectionForm() {
        if (this.state.mode === "single") {
            return this.renderConversionForm();
        }

        const colours = this.state.colours || [];
        const colourHTML = colours.map(colour => `
            <div class="colour-dock-item">
                <div class="colour-swatch" style="background: #${colour}"></div>
                <div style="font-size: 12px; margin-bottom: 8px">#${colour}</div>
                <select id="dock-${colour}" onchange="ui.handleDockChange('${colour}')">
                    <option value="">-- Select Dock --</option>
                    <option value="1">Dock 1</option>
                    <option value="2">Dock 2</option>
                    <option value="3">Dock 3</option>
                    <option value="4">Dock 4</option>
                    <option value="5">Dock 5</option>
                    <option value="6">Dock 6</option>
                </select>
            </div>
        `).join('');

        return `
            <div class="form-section">
                <h2>Step 4: Assign Dock Positions (Multi-Colour)</h2>
                
                <p>
                    Found <strong>${colours.length}</strong> colour(s). Assign each to a dock position.
                </p>

                <div class="colour-picker">
                    ${colourHTML}
                </div>

                <div class="button-group" style="margin-top: 20px;">
                    <button class="secondary" onclick="ui.goBack()">Back</button>
                    <button class="primary" id="convert-btn" onclick="ui.proceedToConversion()">Continue to Conversion</button>
                </div>
            </div>
        `;
    }

    renderConversionForm() {
        return `
            <div class="form-section">
                <h2>Step 5: Ready to Convert</h2>
                
                <div class="alert alert-info">
                    <p><strong>Printer:</strong> ${this.state.printer}</p>
                    <p><strong>Mode:</strong> ${this.state.mode === "single" ? "Single Colour" : "Multi Colour"}</p>
                    <p><strong>Rotation:</strong> ${this.state.rotate ? "Yes" : "No"}</p>
                    <p><strong>Split Compound Paths:</strong> ${this.state.splitCompound ? "Yes" : "No"}</p>
                </div>

                <div class="button-group">
                    <button class="secondary" onclick="ui.goBack()">Back</button>
                    <button class="primary" id="convert-btn" onclick="ui.convert()">Convert to G-Code</button>
                </div>
            </div>
        `;
    }

    renderProcessing(message = "Processing...") {
        const app = document.getElementById("app");
        app.innerHTML = `
            <div class="form-section">
                <div style="text-align: center; padding: 40px;">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            </div>
        `;
    }

    renderResult(result) {
        return `
            <div class="form-section">
                <h2>Conversion Complete!</h2>
                
                <div class="alert alert-success">
                    ✓ Your G-code has been generated successfully!
                </div>

                <div class="dimensions-display">
                    <p><strong>Job ID:</strong> ${result.job_id}</p>
                    <p><strong>Output File:</strong> ${result.gcode}</p>
                </div>

                <div class="button-group">
                    <button class="primary" onclick="ui.init()">Convert Another PDF</button>
                </div>
            </div>
        `;
    }

    attachUploadListeners() {
        document.getElementById("upload-btn").addEventListener("click", () => this.handleUpload());
    }

    async handleUpload() {
        const fileInput = document.getElementById("pdf-upload");
        if (!fileInput.files.length) {
            alert("Please select a PDF file");
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);

        this.renderProcessing("Uploading and analyzing PDF...");

        try {
            const response = await fetch("/analyze/upload", {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error(await response.text());

            const data = await response.json();
            this.state.jobId = data.job_id;
            this.state.uploadPath = data.upload_path;
            this.state.dimensions = data;

            this.currentStep = "config";
            const app = document.getElementById("app");
            app.innerHTML = this.renderConfigForm();
        } catch (error) {
            alert("Upload failed: " + error.message);
            this.init();
        }
    }

    async checkDimensions() {
        this.state.printer = document.getElementById("printer").value;
        this.state.rotate = document.getElementById("rotate").checked;
        this.state.splitCompound = document.getElementById("split-compound").checked;

        this.renderProcessing("Checking dimensions...");

        try {
            const response = await fetch("/analyze/check-dimensions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_id: this.state.jobId,
                    upload_path: this.state.uploadPath,
                    printer: this.state.printer,
                    rotate: this.state.rotate
                })
            });

            if (!response.ok) throw new Error(await response.text());

            const data = await response.json();
            this.state.dimensions = data;

            this.currentStep = "dimension-check";
            const app = document.getElementById("app");
            app.innerHTML = this.renderDimensionCheckForm();
        } catch (error) {
            alert("Dimension check failed: " + error.message);
            this.init();
        }
    }

    async proceedToColours() {
        if (this.state.mode === "single") {
            this.currentStep = "conversion";
            const app = document.getElementById("app");
            app.innerHTML = this.renderConversionForm();
        } else {
            this.renderProcessing("Detecting colours...");

            try {
                const response = await fetch("/analyze/detect-colours", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        job_id: this.state.jobId,
                        upload_path: this.state.uploadPath
                    })
                });

                if (!response.ok) throw new Error(await response.text());

                const data = await response.json();
                this.state.colours = data.colours;

                this.currentStep = "colour-selection";
                const app = document.getElementById("app");
                app.innerHTML = this.renderColourSelectionForm();
            } catch (error) {
                alert("colour detection failed: " + error.message);
                this.currentStep = "config";
                const app = document.getElementById("app");
                app.innerHTML = this.renderConfigForm();
            }
        }
    }

    proceedToConversion() {
        // Validate all docks assigned
        const colours = this.state.colours || [];
        for (const colour of colours) {
            const dock = document.getElementById(`dock-${colour}`).value;
            if (!dock) {
                alert(`Please assign dock position for colour #${colour}`);
                return;
            }
            this.state.dockPositions[colour] = parseInt(dock);
        }

        this.currentStep = "conversion";
        const app = document.getElementById("app");
        app.innerHTML = this.renderConversionForm();
    }

    async convert() {
        this.renderProcessing("Converting to G-code...");

        try {
            const request = {
                printer: this.state.printer,
                mode: this.state.mode,
                line_segments: 50,
                rotate: this.state.rotate,
                scale: null
            };

            if (this.state.mode === "multi") {
                request.dock_positions = this.state.dockPositions;
            }

            const response = await fetch("/convert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_id: this.state.jobId,
                    upload_path: this.state.uploadPath,
                    ...request
                })
            });

            if (!response.ok) throw new Error(await response.text());

            const result = await response.json();
            document.getElementById("app").innerHTML = this.renderResult(result);

        } catch (error) {
            alert("Conversion failed: " + error.message);
            console.error(error);
        }
    }
    
    handlePrinterChange() {
        this.state.printer = document.getElementById("printer").value;
    }

    handleModeChange() {
        this.state.mode = document.querySelector('input[name="mode"]:checked').value;
    }

    handleRotationChange() {
        this.state.rotate = document.getElementById("rotate").checked;
    }

    handleSplitChange() {
        this.state.splitCompound = document.getElementById("split-compound").checked;
    }

    handleDockChange(colour) {
        const dock = document.getElementById(`dock-${colour}`).value;
        if (dock) {
            this.state.dockPositions[colour] = parseInt(dock);
        } else {
            delete this.state.dockPositions[colour];
        }
    }

    goBack() {
        if (this.currentStep === "config") {
            this.init();
        } else if (this.currentStep === "dimension-check") {
            this.currentStep = "config";
            const app = document.getElementById("app");
            app.innerHTML = this.renderConfigForm();
        } else if (this.currentStep === "colour-selection") {
            this.currentStep = "dimension-check";
            const app = document.getElementById("app");
            app.innerHTML = this.renderDimensionCheckForm();
        } else if (this.currentStep === "conversion") {
            if (this.state.mode === "multi") {
                this.currentStep = "colour-selection";
                const app = document.getElementById("app");
                app.innerHTML = this.rendercolourSelectionForm();
            } else {
                this.currentStep = "dimension-check";
                const app = document.getElementById("app");
                app.innerHTML = this.renderDimensionCheckForm();
            }
        }
    }
}

// Initialize UI when page loads
let ui;
document.addEventListener("DOMContentLoaded", () => {
    ui = new InkPrinterUI();
});
